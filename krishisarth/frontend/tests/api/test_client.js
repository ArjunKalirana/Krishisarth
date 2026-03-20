import { api, setToken, clearToken } from '../../src/api/client.js';

const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('API Client', () => {
    beforeEach(() => {
        mockFetch.mockClear();
        clearToken();
        localStorage.clear();
    });

    test('api() attaches Authorization header when token is set', async () => {
        setToken('test-token');
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ success: true })
        });

        await api('/test');
        const options = mockFetch.mock.calls[0][1];
        expect(options.headers['Authorization']).toBe('Bearer test-token');
    });

    test('api() calls refreshAccessToken on 401 response', async () => {
        // First call returns 401
        mockFetch.mockResolvedValueOnce({
            status: 401,
            json: async () => ({ detail: "Expired" })
        });
        
        // Refresh call returns 200
        mockFetch.mockResolvedValueOnce({
            ok: true,
            status: 200,
            json: async () => ({ access_token: "new-token" })
        });

        // Retry call returns 200
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ success: true })
        });

        await api('/protected');
        
        // Successive calls: Original (401), Refresh, Retry (with new token)
        expect(mockFetch).toHaveBeenCalledTimes(3);
        const retryOptions = mockFetch.mock.calls[2][1];
        expect(retryOptions.headers['Authorization']).toBe('Bearer new-token');
    });

    test('api() does not use localStorage for token storage', () => {
        setToken('sensitive-token');
        // Verify token is NOT in localStorage
        const lsValue = Object.values(localStorage).find(v => v === 'sensitive-token');
        expect(lsValue).toBeUndefined();
    });

    test('api() includes credentials: "include" for cookie transmission', async () => {
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({})
        });

        await api('/cookies');
        const options = mockFetch.mock.calls[0][1];
        expect(options.credentials).toBe('include');
    });
});
