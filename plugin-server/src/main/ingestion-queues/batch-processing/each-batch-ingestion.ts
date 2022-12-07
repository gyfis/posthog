import { PluginEvent } from '@posthog/plugin-scaffold'
import { EachBatchPayload, KafkaMessage } from 'kafkajs'

import { Hub, PipelineEvent, WorkerMethods } from '../../../types'
import { formPipelineEvent } from '../../../utils/event'
import { status } from '../../../utils/status'
import { IngestionConsumer } from '../kafka-queue'
import { eachBatch } from './each-batch'

export async function eachMessageIngestion(message: KafkaMessage, queue: IngestionConsumer): Promise<void> {
    await ingestEvent(queue.pluginsServer, queue.workerMethods, formPipelineEvent(message))
}

export async function eachBatchIngestion(payload: EachBatchPayload, queue: IngestionConsumer): Promise<void> {
    function groupIntoBatchesIngestion(kafkaMessages: KafkaMessage[], batchSize: number): KafkaMessage[][] {
        // Once we see a distinct ID we've already seen break up the batch
        const batches = []
        const seenIds: Set<string> = new Set()
        let currentBatch: KafkaMessage[] = []
        for (const message of kafkaMessages) {
            const pluginEvent = formPipelineEvent(message)
            const seenKey = `${pluginEvent.team_id}:${pluginEvent.distinct_id}`
            if (currentBatch.length === batchSize || seenIds.has(seenKey)) {
                seenIds.clear()
                batches.push(currentBatch)
                currentBatch = []
            }
            seenIds.add(seenKey)
            currentBatch.push(message)
        }
        if (currentBatch) {
            batches.push(currentBatch)
        }
        return batches
    }

    if (queue.pluginsServer.UPDATE_LATEST_EVENT_CAPTURED_AT) {
        await updateLatestEventSentAt(payload, queue)
    }

    await eachBatch(payload, queue, eachMessageIngestion, groupIntoBatchesIngestion, 'ingestion')
}

async function updateLatestEventSentAt(payload: EachBatchPayload, queue: IngestionConsumer): Promise<void> {
    // Get the latest sent_at for each token within the batch. We want to
    // minimise the number of PostgreSQL queries we're adding to the pipeline.
    const latestSentAtPerTeam: Record<number, string> = {}
    const teamManager = queue.pluginsServer.teamManager

    for (const message of payload.batch.messages) {
        const token = message.headers?.['api_token']?.toString()
        const teamIdString = message.headers?.['team_id']?.toString()
        const teamId = teamIdString
            ? Number.parseInt(teamIdString)
            : null ?? (token ? (await teamManager.getTeamByToken(token))?.id : null)
        const capturedAt = message.headers?.['captured_at']?.toString()

        if (teamId && capturedAt) {
            latestSentAtPerTeam[teamId] = capturedAt
        }
    }

    // Now update the latest sent_at for each teamId in the batch.
    // TODO: collapse update query into one query?
    status.debug('🔍', `updating_latest_event_captured_at`, { teamIds: Object.keys(latestSentAtPerTeam) })
    for (const [teamId, capturedAt] of Object.entries(latestSentAtPerTeam)) {
        const { rowCount } = await queue.pluginsServer.db.postgresQuery(
            `
            UPDATE posthog_team 
            SET latest_event_captured_at = $1 
            WHERE id = $2 AND (latest_event_captured_at < $1 OR latest_event_captured_at IS NULL)
            `,
            [capturedAt, teamId],
            'setTeamLatestEventSentAt'
        )

        if (rowCount) {
            status.debug('🔍', `updated_latest_event_captured_at`, {
                teamId,
                capturedAt,
                updatedRows: rowCount,
            })
        }
    }
}

export async function ingestEvent(
    server: Hub,
    workerMethods: WorkerMethods,
    event: PipelineEvent,
    checkAndPause?: () => void // pause incoming messages if we are slow in getting them out again
): Promise<void> {
    const eachEventStartTimer = new Date()

    checkAndPause?.()

    // Eventually no events will have a team_id as that will be determined and
    // populated in the plugin server rather than the capture endpoint. However,
    // we support both paths during the transitional period.
    if (event.team_id) {
        server.statsd?.increment('kafka_queue_ingest_event_hit', { pipeline: 'runEventPipeline' })
        // we've confirmed team_id exists so can assert event as PluginEvent
        await workerMethods.runEventPipeline(event as PluginEvent)
    } else {
        server.statsd?.increment('kafka_queue_ingest_event_hit', {
            pipeline: 'runLightweightCaptureEndpointEventPipeline',
        })
        await workerMethods.runLightweightCaptureEndpointEventPipeline(event)
    }

    server.statsd?.timing('kafka_queue.each_event', eachEventStartTimer)

    countAndLogEvents()
}

let messageCounter = 0
let messageLogDate = 0

function countAndLogEvents(): void {
    const now = new Date().valueOf()
    messageCounter++
    if (now - messageLogDate > 10000) {
        status.info(
            '🕒',
            `Processed ${messageCounter} events${
                messageLogDate === 0 ? '' : ` in ${Math.round((now - messageLogDate) / 10) / 100}s`
            }`
        )
        messageCounter = 0
        messageLogDate = now
    }
}
