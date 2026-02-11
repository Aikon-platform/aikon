/**
 * Streaming NDJSON reader for massive pair datasets.
 */

const BATCH_SIZE = 10_000;

/**
 * Stream pairs from server and feed to worker incrementally.
 * @param {string} url - Endpoint URL
 * @param {Worker} worker - Web Worker instance
 * @param {Object} options
 * @param {function} options.onProgress - (pairsLoaded, done) => void
 * @param {function} options.onError - (error) => void
 * @param {AbortSignal} options.signal - AbortController signal
 * @returns {Promise<number>} Total pairs loaded
 */
export async function streamPairsToWorker(url, worker, options = {}) {
    const { onProgress, onError, signal } = options;

    const response = await fetch(url, { signal });

    if (!response.ok) {
        const err = await response.json().catch(() => ({ error: response.statusText }));
        throw new Error(err.error || `HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = '';
    let batch = [];
    let total = 0;
    let initialized = false;

    try {
        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                if (buffer.trim()) {
                    const pair = safeParse(buffer);
                    if (pair) batch.push(pair);
                }

                if (batch.length > 0) {
                    total += batch.length;
                    worker.postMessage({ type: 'batch', pairs: batch, isLast: true });
                } else {
                    worker.postMessage({ type: 'done' });
                }

                onProgress?.(total, true);
                return total;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line) continue;

                const pair = safeParse(line);
                if (!pair) continue;

                batch.push(pair);

                if (batch.length >= BATCH_SIZE) {
                    if (!initialized) {
                        worker.postMessage({ type: 'init' });
                        initialized = true;
                    }

                    total += batch.length;
                    worker.postMessage({ type: 'batch', pairs: batch, isLast: false });
                    batch = [];
                    onProgress?.(total, false);
                }
            }
        }
    } catch (err) {
        if (err.name === 'AbortError') {
            worker.postMessage({ type: 'abort' });
            throw err;
        }
        onError?.(err);
        throw err;
    }
}

function safeParse(line) {
    try {
        return JSON.parse(line);
    } catch {
        console.warn('Parse error:', line.slice(0, 50));
        return null;
    }
}
