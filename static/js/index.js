// Load stats
        fetch('/api/health').then(r=>r.json()).then(d=>{
            document.getElementById('serverStatus').textContent='Online';
            document.getElementById('serverStatus').style.color='#22c55e';
        }).catch(()=>{
            document.getElementById('serverStatus').textContent='Offline';
            document.getElementById('serverStatus').style.color='#ef4444';
        });

        fetch('/api/movie-links').then(r=>r.json()).then(movies=>{
            if(Array.isArray(movies)){
                const approved=movies.filter(m=>m.status==='approved');
                document.getElementById('totalMovies').textContent=approved.length;
                document.getElementById('totalViews').textContent=movies.reduce((s,m)=>s+(m.views||0),0);
            }
        }).catch(()=>{});