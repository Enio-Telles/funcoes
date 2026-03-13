import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';

export interface SSEEvent {
    type: string;
    message: string;
    progress?: number;
    data?: any;
}

export function useSSE() {
    const [events, setEvents] = useState<SSEEvent[]>([]);
    const [currentProgress, setCurrentProgress] = useState<number>(0);
    const [status, setStatus] = useState<string>('idle');
    const [lastMessage, setLastMessage] = useState<string>('');

    const connect = useCallback(() => {
        // API URL is /api/python/events
        const eventSource = new EventSource('/api/python/events');
        setStatus('connecting');

        eventSource.onopen = () => {
            console.log('SSE connection opened');
            setStatus('connected');
        };

        eventSource.onerror = (error) => {
            console.error('SSE connection error:', error);
            setStatus('error');
            eventSource.close();
        };

        eventSource.addEventListener('progress', (event: MessageEvent) => {
            try {
                const data = JSON.parse(event.data);
                setCurrentProgress(data.progress || 0);
                setLastMessage(data.message || '');
                setEvents((prev) => [...prev, { type: 'progress', ...data }]);
            } catch (err) {
                console.error('Error parsing SSE progress data:', err);
            }
        });

        eventSource.addEventListener('complete', (event: MessageEvent) => {
            try {
                const data = JSON.parse(event.data);
                setCurrentProgress(100);
                setLastMessage(data.message || 'Operação concluída');
                setStatus('idle');
                toast.success(data.message || 'Lote processado com sucesso');
                setEvents((prev) => [...prev, { type: 'complete', ...data }]);
            } catch (err) {
                console.error('Error parsing SSE complete data:', err);
            }
        });

        eventSource.addEventListener('error_event', (event: MessageEvent) => {
            try {
                const data = JSON.parse(event.data);
                setStatus('error');
                toast.error(data.message || 'Erro no processamento');
                setEvents((prev) => [...prev, { type: 'error', ...data }]);
            } catch (err) {
                console.error('Error parsing SSE error data:', err);
            }
        });

        return () => {
            eventSource.close();
        };
    }, []);

    return {
        events,
        currentProgress,
        status,
        lastMessage,
        connect,
        setEvents,
        setCurrentProgress,
        setStatus,
    };
}
