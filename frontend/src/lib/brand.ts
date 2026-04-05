export type Brand = 'soulmatesmd' | 'hookupguide';

export function detectBrand(): Brand {
    const host = window.location.hostname;
    // Allow ?brand=hookupguide on localhost for testing
    const params = new URLSearchParams(window.location.search);
    if (params.get('brand') === 'hookupguide') return 'hookupguide';
    if (
        host === 'hookupgui.de' ||
        host === 'www.hookupgui.de' ||
        host.includes('hookupgui')
    ) {
        return 'hookupguide';
    }
    return 'soulmatesmd';
}
