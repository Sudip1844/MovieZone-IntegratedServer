let timerFinished = false;
        let linkData = null;
        let fetchError = null;

        document.addEventListener('DOMContentLoaded', () => {
            const urlParams = new URLSearchParams(window.location.search);
            const shortId = urlParams.get('v');
            
            if (!shortId) {
                document.getElementById('loading').innerHTML = '<h2>Invalid Link</h2><p>No link identifier provided.</p>';
                return;
            }

            // Immediately show UI and start timer
            document.getElementById('loading').style.display = 'none';
            document.getElementById('main-content').style.display = 'block';
            document.getElementById('infoContent').style.display = 'block';
            
            document.getElementById('scrollDownBtn').addEventListener('click', () => {
                window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
            });

            startTimer();
            fetchMovieData(shortId);
        });

        async function fetchMovieData(shortId) {
            try {
                const response = await fetch(`/api/link-info/${shortId}`);
                if (!response.ok) throw new Error('Movie not found');
                const data = await response.json();
                if (data.error) throw new Error(data.error);

                linkData = data;
                document.getElementById('pageTitle').textContent = data.title || "Unknown Movie";
                document.getElementById('pageLabel').textContent = "Download Options";

                const isSingle = data.download_type === 'single';

                // If ads are disabled, finish timer instantly
                if (data.ads_enabled === false) {
                    timerFinished = true;
                    if (isSingle) {
                        document.body.classList.remove('scroll-locked');
                        window.location.href = data.original_link || data.target_link;
                        return;
                    }
                }

                // If timer already finished by the time data arrives, show download button now
                if (timerFinished && !isSingle) {
                    showDownloadButton();
                } else if (timerFinished && isSingle) {
                    showDownloadButton();
                }

            } catch (err) {
                fetchError = err.message;
                document.getElementById('pageTitle').textContent = "Link Expired or Not Found";
                document.getElementById('pageTitle').style.color = "#ef4444";
                document.getElementById('pageLabel').textContent = err.message;
                
                if (timerFinished) {
                    document.getElementById('statusText').textContent = '❌ Failed to get link.';
                }
            }
        }

        function startTimer() {
            let seconds = 10;
            const timer = document.getElementById('timer');
            const progress = document.getElementById('progress');
            const statusText = document.getElementById('statusText');

            const interval = setInterval(() => {
                seconds--;
                timer.textContent = seconds;
                progress.style.width = ((10 - seconds) / 10 * 100) + '%';
                
                if (seconds <= 5 && !timerFinished) statusText.textContent = '⚡ Almost there...';
                
                if (seconds <= 0) {
                    clearInterval(interval);
                    timerFinished = true;
                    timer.textContent = '✅';
                    
                    if (linkData) {
                        showDownloadButton();
                    } else if (fetchError) {
                        statusText.textContent = '❌ Failed to get link.';
                    } else {
                        statusText.textContent = '⏳ Waiting for link data... (Your connection is too slow)';
                    }
                }
            }, 1000);
        }

        function showDownloadButton() {
            document.getElementById('statusText').textContent = '🎉 Your download is ready!';
            document.body.classList.remove('scroll-locked');
            document.getElementById('scrollDownBtn').classList.add('show');
            
            const container = document.getElementById('downloadLinksContainer');
            container.innerHTML = ''; // clear

            if (!linkData) return;

            // Generate header
            let html = `
                <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:25px;margin:40px auto;max-width:600px;text-align:center;">
                    <h2 style="margin:0 0 20px 0;font-size:22px;color:var(--text);">${linkData.title}</h2>
                    <div style="display:flex;flex-direction:column;gap:15px;align-items:center;">
            `;

            if (linkData.download_type === 'single') {
                html += `
                    <a href="${linkData.original_link || '#'}" class="download-btn show" style="width:100%;max-width:300px;">
                        📥 Download Link
                    </a>
                `;
            } else if (linkData.download_type === 'quality' || linkData.download_type === 'zip') {
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
                        const l = ep[`quality${q.charAt(0).toUpperCase() + q.slice(1)}`] || ep[`quality${q}`];
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