document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const shortId = urlParams.get('v');
    
    if (!shortId) {
        document.getElementById('loading').innerHTML = '<h2>Invalid Link</h2><p>No link identifier provided.</p>';
        return;
    }

    fetchMovieData(shortId);
});

async function fetchMovieData(shortId) {
    try {
        const response = await fetch(`/api/link-info/${shortId}`);
        if (!response.ok) throw new Error('Movie not found');
        const data = await response.json();
        if (data.error) throw new Error(data.error);

        document.getElementById('loading').style.display = 'none';

        // Wait... If single, skip rendering container and go straight to URL.
        if (data.download_type === 'single') {
            window.location.href = data.original_link || data.target_link;
            return;
        }

        renderDownloadLinks(data);

    } catch (err) {
        document.getElementById('loading').innerHTML = `
            <h2 style="color:#ef4444;">Link Expired or Not Found</h2>
            <p>${err.message}</p>
        `;
    }
}

function renderDownloadLinks(linkData) {
    const container = document.getElementById('downloadLinksContainer');
    container.innerHTML = '';

    let html = `
        <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:25px;margin:20px auto;max-width:600px;text-align:center;">
            <h2 style="margin:0 0 20px 0;font-size:22px;color:var(--text);">${linkData.title || "Movie Download Options"}</h2>
            <div style="display:flex;flex-direction:column;gap:15px;align-items:center;">
    `;

    if (linkData.download_type === 'quality' || linkData.download_type === 'zip') {
        const isZip = linkData.download_type === 'zip';
        ['480p', '720p', '1080p'].forEach(q => {
            const l = linkData[`quality_${q}`];
            if (l) {
                html += `
                    <div style="display:flex;justify-content:space-between;align-items:center;width:100%;background:rgba(255,255,255,0.05);padding:10px 15px;border-radius:8px;">
                        <span style="font-weight:600;">${isZip ? 'Zip ' : ''}${q} Quality</span>
                        <a href="${l}" class="download-btn show" style="padding:10px 20px;font-size:14px;margin:0;">📥 Download</a>
                    </div>
                `;
            }
        });
    } else if (linkData.download_type === 'episode') {
        let eps = [];
        try { eps = typeof linkData.episodes === 'string' ? JSON.parse(linkData.episodes) : linkData.episodes; } catch(e){}
        
        (eps || []).forEach(ep => {
            html += `<div style="width:100%;text-align:left;margin-top:10px;"><h3 style="margin:0 0 10px 0;font-size:16px;border-bottom:1px solid var(--border);padding-bottom:5px;">Episode ${ep.episodeNumber || ''} ${ep.episodeTitle ? '- ' + ep.episodeTitle : ''}</h3></div>`;
            
            ['480p', '720p', '1080p'].forEach(q => {
                const l = ep['quality' + q] || ep[`quality_${q}`];
                if (l) {
                    html += `
                        <div style="display:flex;justify-content:space-between;align-items:center;width:100%;margin-bottom:8px;background:rgba(255,255,255,0.03);padding:10px 15px;border-radius:8px;">
                            <span style="font-weight:600;font-size:14px;">${q}</span>
                            <a href="${l}" class="download-btn show" style="padding:8px 16px;font-size:13px;margin:0;">📥 Download</a>
                        </div>
                    `;
                }
            });
        });
    }

    html += `</div></div>`;
    container.innerHTML = html;
}
