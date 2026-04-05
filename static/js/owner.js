let allMovies = [];
let pendingMovies = [];
const API = '';

const CATEGORIES = [
    "Bollywood 🇮🇳", "Hollywood 🇺🇸", "South Indian 🎬", "Web Series 🎥",
    "Bengali ✨", "Anime & cartoon 🌀", "Comedy 🤣", "Action 💥",
    "Romance 💑", "Horror 😱", "Thriller 🔍", "Sci-Fi 🛸",
    "K-Drama 🎎", "18+ 🔞", "Mystery 😲", "Crime 🚔",
    "Fantasy 🧿", "Adventure 🗺️", "Documentary 📚", "Drama 🎭"
];
const LANGUAGES = ["Bengali","Hindi","English","Tamil","Telugu","Korean","Gujarati","Malayalam","Chinese","Punjabi","Marathi"];

// Render chips
function renderChips(containerId, items) {
    document.getElementById(containerId).innerHTML = items.map(item =>
        `<button class="chip" onclick="this.classList.toggle('selected')" data-value="${item}">${item}</button>`
    ).join('');
}
function getSelectedChips(containerId) {
    return Array.from(document.querySelectorAll(`#${containerId} .chip.selected`)).map(c => c.dataset.value);
}
renderChips('categoriesContainer', CATEGORIES);
renderChips('languagesContainer', LANGUAGES);

// Thumbnail Preview
function previewThumbnail(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('thumbnailPreview').src = e.target.result;
            document.getElementById('thumbnailPreviewContainer').style.display = 'block';
        }
        reader.readAsDataURL(input.files[0]);
    } else {
        document.getElementById('thumbnailPreviewContainer').style.display = 'none';
        document.getElementById('thumbnailPreview').src = '';
    }
}

// Toggle password visibility
function togglePassVis(inputId, btn) {
    const inp = document.getElementById(inputId);
    if (inp.type === 'password') { inp.type = 'text'; btn.textContent = '🙈'; }
    else { inp.type = 'password'; btn.textContent = '👁️'; }
}

// Toast
function showToast(msg, type='success') {
    const t = document.getElementById('toast');
    t.textContent = msg; t.className = 'toast toast-' + type + ' show';
    setTimeout(() => t.className = 'toast', 3000);
}

// Tabs
function switchTab(name, btn) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    btn.classList.add('active');
    if (name === 'allMovies') loadMovies();
    if (name === 'pending') loadPending();
    if (name === 'admins') loadAdmins();
}

// Download type change
function onTypeChange() {
    const type = document.getElementById('downloadType').value;
    document.querySelectorAll('.dynamic-fields').forEach(f => f.classList.remove('show'));
    document.getElementById('fields-' + type).classList.add('show');
}

// Episode rows
let episodeCount = 0;
function addEpisodeRow() {
    episodeCount++;
    const div = document.createElement('div');
    div.className = 'episode-row';
    div.innerHTML = `
        <span class="ep-num">E1</span>
        <input type="text" placeholder="480p link" class="ep-480">
        <input type="text" placeholder="720p link" class="ep-720">
        <input type="text" placeholder="1080p link" class="ep-1080">
        <button class="btn btn-sm btn-danger" onclick="this.parentElement.remove();renumberEpisodes()">✕</button>
    `;
    document.getElementById('episodeRows').appendChild(div);
    renumberEpisodes();
    validateForm();
}
function renumberEpisodes() {
    let st = parseInt(document.getElementById('epStart').value)||1;
    document.querySelectorAll('.episode-row').forEach((r,i) => {
        r.querySelector('.ep-num').textContent = `E${st+i}`;
    });
    validateForm();
}
addEpisodeRow();

// Validation logic for Add Movie
document.addEventListener('input', (e) => {
    if (['movieThumbnail','movieTitle','singleLink','q480','q720','q1080','zip480','zip720','zip1080'].includes(e.target.id)) {
        validateForm();
    }
});
function checkDropdownClick(e) {
    if (e.target.classList.contains('chip')) {
        validateForm();
        updatePreviewChips('editCategoriesContainer', 'editCatPreview');
        updatePreviewChips('editLanguagesContainer', 'editLangPreview');
    }
}
document.addEventListener('click', checkDropdownClick);

function clearError(fgId) {
    const el = document.getElementById(fgId);
    if (el) el.classList.remove('has-error');
    validateForm();
}
function showFieldErrors() {
    const thumb = document.getElementById('movieThumbnail').files.length > 0;
    const title = document.getElementById('movieTitle').value.trim().length > 0;
    const cats = getSelectedChips('categoriesContainer').length > 0;
    const langs = getSelectedChips('languagesContainer').length > 0;
    const type = document.getElementById('downloadType').value;
    let hasLink = false;
    if (type === 'single') hasLink = document.getElementById('singleLink').value.trim() !== '';
    else if (type === 'quality') hasLink = ['q480','q720','q1080'].some(id => document.getElementById(id).value.trim() !== '');
    else if (type === 'zip') hasLink = ['zip480','zip720','zip1080'].some(id => document.getElementById(id).value.trim() !== '');
    else if (type === 'episode') hasLink = document.querySelectorAll('.episode-row').length > 0;
    if (!thumb) document.getElementById('fg-thumbnail')?.classList.add('has-error');
    if (!title) document.getElementById('fg-title')?.classList.add('has-error');
    if (!cats) document.getElementById('fg-categories')?.classList.add('has-error');
    if (!langs) document.getElementById('fg-languages')?.classList.add('has-error');
    if (!hasLink && type === 'single') document.getElementById('fg-singleLink')?.classList.add('has-error');
}
function validateForm() {
    const thumb = document.getElementById('movieThumbnail').files.length > 0;
    const title = document.getElementById('movieTitle').value.trim().length > 0;
    const cats = getSelectedChips('categoriesContainer').length > 0;
    const langs = getSelectedChips('languagesContainer').length > 0;
    const type = document.getElementById('downloadType').value;
    
    let hasLink = false;
    if (type === 'single') hasLink = document.getElementById('singleLink').value.trim() !== '';
    else if (type === 'quality') hasLink = ['q480','q720','q1080'].some(id => document.getElementById(id).value.trim() !== '');
    else if (type === 'zip') hasLink = ['zip480','zip720','zip1080'].some(id => document.getElementById(id).value.trim() !== '');
    else if (type === 'episode') hasLink = document.querySelectorAll('.episode-row').length > 0;
    
    const btn = document.getElementById('addBtn');
    // Button is no longer disabled. Validation is handled on click.
}

// Close dropdowns if clicked outside
document.addEventListener('click', (e) => {
    if(!e.target.closest('#editCatDropdownContainer')) document.getElementById('editCatDropdownContainer')?.classList.remove('open');
    if(!e.target.closest('#editLangDropdownContainer')) document.getElementById('editLangDropdownContainer')?.classList.remove('open');
});

// Sync chips to preview
function updatePreviewChips(containerId, previewId) {
    const chips = getSelectedChips(containerId);
    const pv = document.getElementById(previewId);
    if (!pv) return;
    if (!chips.length) {
        pv.innerHTML = `<span class="preview-placeholder">Select...</span>`;    
    } else {
        pv.innerHTML = chips.map(c => `<span class="preview-chip">${c}</span>`).join('');
    }
}

// Login
async function doLogin() {
    const id = document.getElementById('loginId').value.trim();
    const pass = document.getElementById('loginPass').value.trim();
    if (!id || !pass) return showToast('Enter credentials', 'error');
    try {
        const r = await fetch(API + '/api/admin-login', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({adminId:id,adminPassword:pass}) });
        const d = await r.json();
        if (d.success) {
            document.getElementById('roleBadge').textContent = d.role.toUpperCase();
            document.getElementById('loginScreen').style.display = 'none';
            document.getElementById('dashboard').style.display = 'block';
            localStorage.setItem('mz_logged', '1');
            localStorage.setItem('mz_role', d.role);
            loadStats();
            showToast('Welcome back!');
        } else showToast(d.error || 'Invalid credentials', 'error');
    } catch(e) { showToast('Login failed', 'error'); }
}
function doLogout() {
    localStorage.removeItem('mz_logged');
    localStorage.removeItem('mz_role');
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('loginScreen').style.display = 'flex';
}
if (localStorage.getItem('mz_logged')) {
    document.getElementById('roleBadge').textContent = (localStorage.getItem('mz_role')||'owner').toUpperCase();
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    loadStats();
}

// Stats
async function loadStats() {
    try {
        const [movies, pending, admins] = await Promise.all([
            fetch(API+'/api/movie-links').then(r=>r.json()),
            fetch(API+'/api/pending-movies').then(r=>r.json()),
            fetch(API+'/api/admin-accounts').then(r=>r.json())
        ]);
        allMovies = Array.isArray(movies) ? movies : [];
        const pend = Array.isArray(pending) ? pending : [];
        document.getElementById('statMovies').textContent = allMovies.length;
        document.getElementById('statViews').textContent = allMovies.reduce((s,m)=>s+(m.views||0),0);
        document.getElementById('statPending').textContent = pend.length;
        document.getElementById('statAdmins').textContent = Array.isArray(admins) ? admins.length : 0;
    } catch(e) { console.error(e); }
}

// RESET FORM
function resetAddForm() {
    document.getElementById('movieTitle').value = '';
    document.getElementById('singleLink').value = '';
    document.getElementById('q480').value = '';
    document.getElementById('q720').value = '';
    document.getElementById('q1080').value = '';
    document.getElementById('zip480').value = '';
    document.getElementById('zip720').value = '';
    document.getElementById('zip1080').value = '';
    document.getElementById('zipFrom').value = '';
    document.getElementById('zipTo').value = '';
    document.getElementById('releaseYear').value = '';
    document.getElementById('runtime').value = '';
    document.getElementById('imdbRating').value = '';
    document.getElementById('movieThumbnail').value = '';
    document.getElementById('thumbnailPreviewContainer').style.display = 'none';
    document.getElementById('thumbnailPreview').src = '';
    document.getElementById('downloadType').value = 'single';
    onTypeChange();
    document.querySelectorAll('.chip.selected').forEach(c => c.classList.remove('selected'));
    document.getElementById('episodeRows').innerHTML = '';
    episodeCount = 0;
    addEpisodeRow();
    validateForm();
}

// ADD MOVIE (unified)
async function addMovie() {
    const title = document.getElementById('movieTitle').value.trim();
    const type = document.getElementById('downloadType').value;
    const categories = getSelectedChips('categoriesContainer');
    const languages = getSelectedChips('languagesContainer');
    const thumbnailFile = document.getElementById('movieThumbnail').files[0];
    
    let hasLink = false;
    if (type === 'single') hasLink = document.getElementById('singleLink').value.trim() !== '';
    else if (type === 'quality') hasLink = ['q480','q720','q1080'].some(id => document.getElementById(id).value.trim() !== '');
    else if (type === 'zip') hasLink = document.getElementById('zipFrom').value.trim() !== '' && document.getElementById('zipTo').value.trim() !== '' && ['zip480','zip720','zip1080'].some(id => document.getElementById(id).value.trim() !== '');
    else if (type === 'episode') hasLink = document.querySelectorAll('.episode-row').length > 0;

    if (!title || categories.length === 0 || languages.length === 0 || !thumbnailFile || !hasLink) {
        showFieldErrors();
        let missed = [];
        if (!title) missed.push("Movie Title");
        if (categories.length === 0) missed.push("Categories");
        if (languages.length === 0) missed.push("Languages");
        if (!hasLink) missed.push("Download Link(s)");
        if (!thumbnailFile) missed.push("Thumbnail");
        return showToast("Required: " + missed.join(', '), 'error');
    }

    const releaseYear = document.getElementById('releaseYear').value.trim() || 'N/A';
    const runtime = document.getElementById('runtime').value.trim() || 'N/A';
    const imdbRating = document.getElementById('imdbRating').value.trim() || 'N/A';
    const adsEnabled = document.getElementById('adsToggle').classList.contains('on');

    let body = {
        title, downloadType: type, categories, languages,
        releaseYear, runtime, imdbRating, adsEnabled, status: 'pending',
        addedBy: 'owner'
    };

    if (type === 'single') {
        body.originalLink = document.getElementById('singleLink').value.trim();
        if (!body.originalLink) return showToast('Enter download link', 'error');
    } else if (type === 'quality') {
        body.quality480p = document.getElementById('q480').value.trim() || null;
        body.quality720p = document.getElementById('q720').value.trim() || null;
        body.quality1080p = document.getElementById('q1080').value.trim() || null;
        if (!body.quality480p && !body.quality720p && !body.quality1080p) return showToast('Enter at least one quality link', 'error');
    } else if (type === 'episode') {
        const startFrom = parseInt(document.getElementById('epStart').value) || 1;
        const rows = document.querySelectorAll('.episode-row');
        const episodes = [];
        rows.forEach((row, i) => {
            episodes.push({
                episodeNumber: startFrom + i,
                quality480p: row.querySelector('.ep-480').value.trim(),
                quality720p: row.querySelector('.ep-720').value.trim(),
                quality1080p: row.querySelector('.ep-1080').value.trim()
            });
        });
        body.episodes = JSON.stringify(episodes);
        body.startFromEpisode = startFrom;
    } else if (type === 'zip') {
        body.fromEpisode = parseInt(document.getElementById('zipFrom').value);
        body.toEpisode = parseInt(document.getElementById('zipTo').value);
        body.quality480p = document.getElementById('zip480').value.trim() || null;
        body.quality720p = document.getElementById('zip720').value.trim() || null;
        body.quality1080p = document.getElementById('zip1080').value.trim() || null;
        if (!body.fromEpisode || !body.toEpisode) return showToast('Enter episode range', 'error');
        if (!body.quality480p && !body.quality720p && !body.quality1080p) return showToast('Enter at least one zip link', 'error');
    }

    // removed redeclaration of thumbnailFile here
    const overlay = document.createElement('div');
    overlay.id = 'uploadOverlay';
    overlay.innerHTML = '<div style="position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,0,0,0.8);z-index:9999;display:flex;flex-direction:column;justify-content:center;align-items:center;color:white;font-size:24px;"><div>Uploading Movie & Generating Links...</div><div class="loader" style="margin-top:20px;border-width:4px;width:40px;height:40px;border-color:#fff transparent transparent transparent;border-style:solid;border-radius:50%;animation:spin 1s linear infinite;"></div><style>@keyframes spin{0%{transform:rotate(0)}100%{transform:rotate(360deg)}}</style></div>';
    document.body.appendChild(overlay);

    let formData = new FormData();
    formData.append('data', JSON.stringify(body));
    formData.append('thumbnail', thumbnailFile);

    try {
        const r = await fetch(API + '/api/movie-links', {
            method: 'POST', body: formData
        });
        const d = await r.json();
        if (document.getElementById('uploadOverlay')) document.getElementById('uploadOverlay').remove();

        if (d.success || d.shortUrl) {
            const container = document.getElementById('addLinksContainer');
            let html = '';
            if (d.shortUrls && Object.keys(d.shortUrls).length > 0) {
                for (const [key, url] of Object.entries(d.shortUrls)) {
                    let label = key;
                    if (key.startsWith('zip_')) label = `Zip: ${key.replace('zip_', '')}`;
                    else if (key.startsWith('e')) {
                        const parts = key.match(/e(\d+)_(.+)/);
                        if (parts) label = `Ep ${parts[1]} (${parts[2]})`;
                    } else if (['480p','720p','1080p'].includes(key)) {
                        label = `Quality: ${key}`;
                    } else if (key === 'original') {
                        label = 'Link';
                    }
                    html += `<div class="link-item"><span style="color:var(--primary);font-weight:bold;margin-right:8px;">${label}:</span><span>${url}</span><button class="copy-icon" style="margin-left:auto" onclick="copyUrl('${url}')">📋</button></div>`;
                }
            } else {
                html = `<div class="link-item"><span>${d.shortUrl || 'Submitted for review'}</span><button class="copy-icon" onclick="copyUrl('${d.shortUrl}')">📋</button></div>`;
            }
            container.innerHTML = html;
            document.getElementById('addResult').classList.add('show');

            resetAddForm();
            showToast('Movie submitted for review!');
            loadStats();

            setTimeout(() => {
                document.getElementById('addResult').classList.remove('show');
            }, 15000);
        } else {
            showToast(d.error || 'Failed', 'error');
        }
    } catch(e) { 
        if (document.getElementById('uploadOverlay')) document.getElementById('uploadOverlay').remove();
        showToast('Error: ' + e.message, 'error'); 
    }
}

function copyUrl(url) {
    navigator.clipboard.writeText(url).then(()=>showToast('Copied!')).catch(()=>showToast('Copy failed','error'));
}

// ALL MOVIES (approved only)
async function loadMovies(btn = null) {
    if (btn) {
        btn.classList.add('spinning');
        btn.disabled = true;
    }
    try {
        const r = await fetch(API + '/api/movie-links');
        allMovies = await r.json();
        if (!Array.isArray(allMovies)) allMovies = [];
        filterMovies();
    } catch(e) { showToast('Failed to load', 'error'); }
    if (btn) {
        setTimeout(() => {
            btn.classList.remove('spinning');
            btn.disabled = false;
        }, 500); // minimum 500ms spin for effect
    }
}

function filterMovies() {
    const search = (document.getElementById('searchInput').value || '').toLowerCase();
    const sort = document.getElementById('sortSelect').value;
    let f = allMovies.filter(m => (m.title||'').toLowerCase().includes(search));
    if (sort === 'date_desc') f.sort((a,b)=>(b.created_at||'').localeCompare(a.created_at||''));
    else if (sort === 'date_asc') f.sort((a,b)=>(a.created_at||'').localeCompare(b.created_at||''));
    else if (sort === 'name_asc') f.sort((a,b)=>(a.title||'').localeCompare(b.title||''));
    else if (sort === 'name_desc') f.sort((a,b)=>(b.title||'').localeCompare(a.title||''));

    const tbody = document.getElementById('moviesTable');
    if (!f.length) { tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text-secondary)">No movies found</td></tr>'; return; }
    tbody.innerHTML = f.map((m, idx) => {
        let urlDisplayHtml = '—';
        if (m.short_id) {
            let shortIdsObj = null;
            if (m.short_ids) {
                try { shortIdsObj = typeof m.short_ids === 'string' ? JSON.parse(m.short_ids) : m.short_ids; } catch(e) {}
            }
            
            const mainUrl = `${location.origin}/m/${m.short_id}`;
            
            if (shortIdsObj && Object.keys(shortIdsObj).length > 1) {
                let dropdownList = [];
                for (const [key, sid] of Object.entries(shortIdsObj)) {
                    if (key === 'original') continue;
                    const url = `${location.origin}/m/${sid}`;
                    
                    let label = key;
                    if (key.startsWith('zip_')) label = `Zip: ${key.replace('zip_', '')}`;
                    else if (key.startsWith('e')) {
                        const parts = key.match(/e(\d+)_(.+)/);
                        if (parts) label = `Ep ${parts[1]} (${parts[2]})`;
                    } else if (['480p','720p','1080p'].includes(key)) {
                        label = `Quality: ${key}`;
                    }
                    
                    dropdownList.push(`
                        <div class="shortlink-item">
                            <span class="shortlink-label">${label}</span>
                            <span class="shortlink-url">${url}</span>
                            <button class="copy-icon" onclick="copyUrl('${url}')">📋</button>
                        </div>
                    `);
                }
                
                urlDisplayHtml = `
                    <div class="shortlink-container">
                        <div class="shortlink-main">
                            <span>${mainUrl}</span>
                            <button class="copy-icon" onclick="copyUrl('${mainUrl}')">📋</button>
                            <button class="dropdown-icon-btn" onclick="this.nextElementSibling.classList.toggle('show')">▼</button>
                            <div class="shortlink-dropdown">
                                ${dropdownList.join('')}
                            </div>
                        </div>
                    </div>
                `;
            } else {
                urlDisplayHtml = `<span>${mainUrl}</span> <button class="copy-icon" onclick="copyUrl('${mainUrl}')">📋</button>`;
            }
        }

        const addedBy = m.added_by || 'owner';
        const adsEnabled = m.ads_enabled !== false;
        return `<tr>
            <td>${idx + 1}</td>
            <td><strong>${esc(m.title||'')}</strong></td>
            <td>${m.download_type||'single'}</td>
            <td>${esc(addedBy)}</td>
            <td>${m.views||0}</td>
            <td>
                <div class="toggle" style="justify-content:center">
                    <div class="toggle-switch ${adsEnabled ? 'on' : ''}" onclick="toggleMovieAds(${m.id}, ${!adsEnabled})" title="${adsEnabled ? 'Ads On' : 'Ads Off'}"></div>
                </div>
            </td>
            <td style="font-size:0.75rem;max-width:200px;overflow:visible;">
                ${urlDisplayHtml}
            </td>
            <td><div class="actions">
                <button class="btn btn-sm btn-outline" onclick="openEdit(${m.id})">✏️</button>
                <button class="btn btn-sm btn-danger" onclick="deleteMovie(${m.id})">🗑️</button>
            </div></td>
        </tr>`;
    }).join('');
}
function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

// EDIT MOVIE - shows correct fields based on type
function openEdit(id) {
    const m = allMovies.find(x=>x.id===id); if(!m) return;
    const dtype = m.download_type || 'single';
    document.getElementById('editId').value = id;
    document.getElementById('editType').value = dtype;
    document.getElementById('editTitle').value = m.title||'';

    document.getElementById('editFields-single').style.display = 'none';
    document.getElementById('editFields-quality').style.display = 'none';

    if (dtype === 'single') {
        document.getElementById('editFields-single').style.display = 'block';
        document.getElementById('editOrigLink').value = m.original_link||'';
    } else if (dtype === 'quality' || dtype === 'zip') {
        document.getElementById('editFields-quality').style.display = 'block';
        document.getElementById('editQ480').value = m.quality_480p||'';
        document.getElementById('editQ720').value = m.quality_720p||'';
        document.getElementById('editQ1080').value = m.quality_1080p||'';
    }

    renderChips('editCategoriesContainer', CATEGORIES);
    renderChips('editLanguagesContainer', LANGUAGES);

    const categories = Array.isArray(m.categories) ? m.categories : [];
    document.querySelectorAll('#editCategoriesContainer .chip').forEach(c => {
        if (categories.includes(c.dataset.value)) c.classList.add('selected');
    });
    const languages = Array.isArray(m.languages) ? m.languages : [];
    document.querySelectorAll('#editLanguagesContainer .chip').forEach(c => {
        if (languages.includes(c.dataset.value)) c.classList.add('selected');
    });

    updatePreviewChips('editCategoriesContainer', 'editCatPreview');
    updatePreviewChips('editLanguagesContainer', 'editLangPreview');

    document.getElementById('editYear').value = m.release_year === 'N/A' ? '' : (m.release_year || '');
    document.getElementById('editRuntime').value = m.runtime === 'N/A' ? '' : (m.runtime || '');
    document.getElementById('editImdb').value = m.imdb_rating === 'N/A' ? '' : (m.imdb_rating || '');

    const adsEnabled = m.ads_enabled !== false;
    if (adsEnabled) document.getElementById('editAdsToggle').classList.add('on');
    else document.getElementById('editAdsToggle').classList.remove('on');

    document.getElementById('editModal').classList.add('show');
}
function closeModal() { document.getElementById('editModal').classList.remove('show'); }
async function saveEdit() {
    const id = document.getElementById('editId').value;
    const dtype = document.getElementById('editType').value;
    const data = { 
        title: document.getElementById('editTitle').value.trim(),
        categories: getSelectedChips('editCategoriesContainer'),
        languages: getSelectedChips('editLanguagesContainer'),
        release_year: document.getElementById('editYear').value.trim() || 'N/A',
        runtime: document.getElementById('editRuntime').value.trim() || 'N/A',
        imdb_rating: document.getElementById('editImdb').value.trim() || 'N/A',
        ads_enabled: document.getElementById('editAdsToggle').classList.contains('on')
    };

    if (dtype === 'single') {
        data.original_link = document.getElementById('editOrigLink').value.trim();
    } else if (dtype === 'quality' || dtype === 'zip') {
        data.quality_480p = document.getElementById('editQ480').value.trim()||null;
        data.quality_720p = document.getElementById('editQ720').value.trim()||null;
        data.quality_1080p = document.getElementById('editQ1080').value.trim()||null;
    }
    try { await fetch(API+`/api/movie-links/${id}`, {method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}); closeModal(); showToast('Updated!'); loadMovies(); } catch(e) { showToast('Failed','error'); }
}
let pendingDeleteId = null;
let pendingDeleteType = 'movie';
function closeDeleteConfirm() { document.getElementById('deleteConfirmModal').classList.remove('show'); pendingDeleteId = null; }

function deleteMovie(id) {
    const m = allMovies.find(x => x.id === id);
    pendingDeleteId = id;
    pendingDeleteType = 'movie';
    document.getElementById('deleteConfirmTitle').textContent = 'Delete Movie?';
    document.getElementById('deleteConfirmText').textContent = m ? `"${m.title}" will be permanently deleted.` : 'This movie will be permanently deleted.';
    document.getElementById('deleteConfirmModal').classList.add('show');
    document.getElementById('deleteConfirmYes').onclick = async () => {
        const idToDelete = pendingDeleteId;
        closeDeleteConfirm();
        try { await fetch(API+`/api/movie-links/${idToDelete}`,{method:'DELETE'}); showToast('Deleted'); loadMovies(); loadStats(); } catch(e) { showToast('Failed','error'); }
    };
}

async function toggleMovieAds(id, adsEnabled) {
    try {
        await fetch(API+`/api/movie-links/${id}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ ads_enabled: adsEnabled })
        });
        showToast(adsEnabled ? 'Ads Enabled' : 'Ads Disabled');
        loadMovies();
    } catch(e) { showToast('Failed', 'error'); }
}

// PENDING - with details popup
async function loadPending() {
    try {
        const r = await fetch(API+'/api/pending-movies');
        pendingMovies = await r.json();
        const el = document.getElementById('pendingList');
        if (!pendingMovies.length) { el.innerHTML = '<p style="text-align:center;padding:40px;color:var(--text-secondary)">🎉 No pending movies!</p>'; return; }
        el.innerHTML = pendingMovies.map(m => {
            const cats = Array.isArray(m.categories) ? m.categories.join(', ') : (m.categories||'');
            return `<div class="pending-card">
                <div class="pending-info">
                    <strong>${esc(m.title||'')}</strong>
                    <span class="badge badge-pending" style="margin-left:8px">${m.download_type||'single'}</span>
                    <div class="pending-meta">Added by: ${esc(m.added_by||'owner')} • ${cats ? cats : 'No categories'}</div>
                </div>
                <div class="actions">
                    <button class="btn btn-sm btn-outline" onclick="showPendingDetail(${m.id})">📋 Details</button>
                    <button class="btn btn-sm btn-success" onclick="approvePending(${m.id})">✅</button>
                    <button class="btn btn-sm btn-danger" onclick="rejectPending(${m.id})">❌</button>
                </div>
            </div>`;
        }).join('');
    } catch(e) { showToast('Failed','error'); }
}

// Show pending detail popup (telegram-style)
function showPendingDetail(id) {
    const m = pendingMovies.find(x=>x.id===id); if(!m) return;
    const cats = Array.isArray(m.categories) ? m.categories.join(', ') : (m.categories||'N/A');
    const langs = Array.isArray(m.languages) ? m.languages.join(', ') : (m.languages||'N/A');
    const dtype = m.download_type || 'single';

    let linksHtml = '';
    if (dtype === 'single') {
        linksHtml = `<div><span class="label">🔗 Download Link:</span><br><span class="link-val">${esc(m.original_link||'N/A')}</span></div>`;
    } else if (dtype === 'quality' || dtype === 'zip') {
        if (m.quality_480p) linksHtml += `<div><span class="label">📥 480p:</span> <span class="link-val">${esc(m.quality_480p)}</span></div>`;
        if (m.quality_720p) linksHtml += `<div><span class="label">📥 720p:</span> <span class="link-val">${esc(m.quality_720p)}</span></div>`;
        if (m.quality_1080p) linksHtml += `<div><span class="label">📥 1080p:</span> <span class="link-val">${esc(m.quality_1080p)}</span></div>`;
    } else if (dtype === 'episode') {
        let eps = [];
        try { eps = typeof m.episodes === 'string' ? JSON.parse(m.episodes) : (m.episodes||[]); } catch(e){}
        linksHtml = `<div><span class="label">📺 Episodes:</span> ${eps.length} episode(s)</div>`;
        eps.forEach(ep => {
            linksHtml += `<div style="margin-left:12px"><span class="label">E${ep.episodeNumber||'?'}:</span>`;
            if (ep.quality480p) linksHtml += ` 480p `;
            if (ep.quality720p) linksHtml += ` 720p `;
            if (ep.quality1080p) linksHtml += ` 1080p `;
            linksHtml += `</div>`;
        });
    }
    if (dtype === 'zip') {
        linksHtml = `<div><span class="label">📦 Zip Range:</span> <span class="value">Episode ${m.from_episode||'?'} - ${m.to_episode||'?'}</span></div>` + linksHtml;
    }

    const html = `
        <div class="detail-preview">
            <div><span class="label">🎬 Title:</span> <span class="value">${esc(m.title||'')}</span></div>
            <div><span class="label">📁 Type:</span> <span class="value">${dtype.toUpperCase()}</span></div>
            <div><span class="label">👤 Added By:</span> <span class="value">${esc(m.added_by||'owner')}</span></div>
            <br>
            ${linksHtml}
            <br>
            <div><span class="label">🏷️ Categories:</span> <span class="value">${esc(cats)}</span></div>
            <div><span class="label">🌐 Languages:</span> <span class="value">${esc(langs)}</span></div>
            <div><span class="label">📅 Release Year:</span> <span class="value">${esc(m.release_year||'N/A')}</span></div>
            <div><span class="label">⏱️ Runtime:</span> <span class="value">${esc(m.runtime||'N/A')}</span></div>
            <div><span class="label">⭐ IMDb:</span> <span class="value">${esc(m.imdb_rating||'N/A')}</span></div>
            <div><span class="label">📢 Ads:</span> <span class="value">${m.ads_enabled !== false ? 'Enabled' : 'Disabled'}</span></div>
        </div>`;

    document.getElementById('pendingDetailContent').innerHTML = html;
    document.getElementById('pendingApproveBtn').onclick = () => { approvePending(id); closePendingDetail(); };
    document.getElementById('pendingRejectBtn').onclick = () => { rejectPending(id); closePendingDetail(); };
    document.getElementById('pendingDetailModal').classList.add('show');
}
function closePendingDetail() { document.getElementById('pendingDetailModal').classList.remove('show'); }

async function approvePending(id) { try { await fetch(API+`/api/movies/${id}/approve`,{method:'POST'}); showToast('Approved!'); loadPending(); loadStats(); } catch(e) { showToast('Failed','error'); } }
async function rejectPending(id) { try { await fetch(API+`/api/movies/${id}/reject`,{method:'POST'}); showToast('Rejected'); loadPending(); loadStats(); } catch(e) { showToast('Failed','error'); } }

// ADMINS
async function loadAdmins() {
    try {
        const r = await fetch(API+'/api/admin-accounts');
        const a = await r.json();
        const tbody = document.getElementById('adminsTable');
        if (!a.length) { tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--text-secondary)">No admin accounts</td></tr>'; return; }
        tbody.innerHTML = a.map(x => `<tr>
            <td><strong>${esc(x.admin_id)}</strong></td>
            <td style="font-family:monospace;font-size:0.8rem">${esc(x.admin_password||'')}</td>
            <td>${esc(x.display_name||'')}</td>
            <td><span class="badge ${x.is_active?'badge-approved':'badge-rejected'}">${x.is_active?'Active':'Disabled'}</span></td>
            <td>${(x.created_at||'').slice(0,10)}</td>
            <td><div class="actions">
                <button class="btn btn-sm btn-outline" onclick="openAdminEdit(${x.id},'${esc(x.admin_id)}','${esc(x.admin_password||'')}','${esc(x.display_name||'')}')">✏️</button>
                <button class="btn btn-sm btn-${x.is_active?'warning':'success'}" onclick="toggleAdmin(${x.id},${!x.is_active})">${x.is_active?'Disable':'Enable'}</button>
                <button class="btn btn-sm btn-danger" onclick="deleteAdmin(${x.id})">🗑️</button>
            </div></td>
        </tr>`).join('');
    } catch(e) { showToast('Failed','error'); }
}
async function createAdmin() {
    const id=document.getElementById('newAdminId').value.trim(), pass=document.getElementById('newAdminPass').value.trim(), name=document.getElementById('newAdminName').value.trim();
    if (!id || !pass || !name) return showToast('ID, Password, and Display Name are required','error');
    try { const r = await fetch(API+'/api/admin-accounts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({adminId:id,adminPassword:pass,displayName:name})}); const d=await r.json(); if(d.success){showToast('Created!');['newAdminId','newAdminPass','newAdminName'].forEach(i=>document.getElementById(i).value='');loadAdmins();loadStats();} else showToast(d.error||'Failed','error'); } catch(e){showToast('Error','error');}
}
async function toggleAdmin(id,active) { try { await fetch(API+`/api/admin-accounts/${id}/toggle`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({isActive:active})}); showToast('Updated'); loadAdmins(); } catch(e){showToast('Failed','error');} }
function deleteAdmin(id) {
    pendingDeleteId = id;
    pendingDeleteType = 'admin';
    document.getElementById('deleteConfirmTitle').textContent = 'Delete Admin?';
    document.getElementById('deleteConfirmText').textContent = 'This admin account will be permanently deleted.';
    document.getElementById('deleteConfirmModal').classList.add('show');
    document.getElementById('deleteConfirmYes').onclick = async () => {
        const idToDelete = pendingDeleteId;
        closeDeleteConfirm();
        try { await fetch(API+`/api/admin-accounts/${idToDelete}`,{method:'DELETE'}); showToast('Deleted'); loadAdmins(); loadStats(); } catch(e){showToast('Failed','error');}
    };
}

function openAdminEdit(id, adminId, adminPass, displayName) {
    document.getElementById('editAdminRowId').value = id;
    document.getElementById('editAdminId').value = adminId;
    document.getElementById('editAdminPass').value = adminPass;
    document.getElementById('editAdminName').value = displayName;
    document.getElementById('editAdminModal').classList.add('show');
}
function closeAdminModal() { document.getElementById('editAdminModal').classList.remove('show'); }
async function saveAdminEdit() {
    const id = document.getElementById('editAdminRowId').value;
    const data = {
        adminId: document.getElementById('editAdminId').value.trim(),
        adminPassword: document.getElementById('editAdminPass').value,
        displayName: document.getElementById('editAdminName').value.trim()
    };
    if (!data.adminId) return showToast('Admin ID required', 'error');
    try {
        const r = await fetch(API+`/api/admin-accounts/${id}`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
        const d = await r.json();
        if (d.success) { closeAdminModal(); showToast('Admin updated!'); loadAdmins(); }
        else showToast(d.error || 'Failed', 'error');
    } catch(e) { showToast('Error','error'); }
}