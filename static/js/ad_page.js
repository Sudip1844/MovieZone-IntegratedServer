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

                // If ads are disabled, redirect instantly regardless of timer
                if (data.ads_enabled === false) {
                    document.body.classList.remove('scroll-locked');
                    window.location.href = data.target_link;
                    return;
                }

                linkData = data;
                document.getElementById('pageTitle').textContent = data.title || "Unknown Movie";
                document.getElementById('pageLabel').textContent = data.link_label || "Download";
                document.getElementById('btnLabel').textContent = data.link_label || "Download";
                document.getElementById('downloadBtn').href = data.target_link;

                // If timer already finished by the time data arrives, show download button now
                if (timerFinished) {
                    showDownloadButton();
                }

            } catch (err) {
                fetchError = err.message;
                document.getElementById('pageTitle').textContent = "Link Expired or Not Found";
                document.getElementById('pageTitle').style.color = "#ef4444";
                document.getElementById('pageLabel').textContent = err.message;
                
                // If timer is already done, update status
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
            document.getElementById('downloadBtn').classList.add('show');
            document.body.classList.remove('scroll-locked');
            document.getElementById('scrollDownBtn').classList.add('show');
        }