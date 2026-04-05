const API = '';
let currentAdminId = '';
let currentAdminName = '';

const CATEGORIES = [
    "Bollywood 🇮🇳", "Hollywood 🇺🇸", "South Indian 🎬", "Web Series 🎥",
    "Bengali ✨", "Anime & cartoon 🌀", "Comedy 🤣", "Action 💥",
    "Romance 💑", "Horror 😱", "Thriller 🔍", "Sci-Fi 🛸",
    "K-Drama 🎎", "18+ 🔞", "Mystery 😲", "Crime 🚔",
    "Fantasy 🧿", "Adventure 🗺️", "Documentary 📚", "Drama 🎭"
];
const LANGUAGES = ["Bengali","Hindi","English","Tamil","Telugu","Korean","Gujarati","Malayalam","Chinese","Punjabi","Marathi"];

function renderChips(id, items) {
    document.getElementById(id).innerHTML = items.map(i =>
        `<button class="chip" onclick="this.classList.toggle('selected')" data-value="${i}">${i}</button>`
    ).join('');
}
function getSelectedChips(id) {
    return Array.from(document.querySelectorAll(`#${id} .chip.selected`)).map(c => c.dataset.value);
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

function togglePassVis(inputId, btn) {
    const inp = document.getElementById(inputId);
    if (inp.type === 'password') { inp.type = 'text'; btn.textContent = '🙈'; }
    else { inp.type = 'password'; btn.textContent = '👁️'; }
}

function showToast(msg, type='success') {
    const t = document.getElementById('toast');
    t.textContent = msg; t.className = 'toast toast-' + type + ' show';
    setTimeout(() => t.className = 'toast', 3000);
}

function switchTab(name, btn) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + name).classList.add('active');
    btn.classList.add('active');
    if (name === 'myMovies') loadMyMovies();
}

function onTypeChange() {
    const type = document.getElementById('downloadType').value;
    document.querySelectorAll('.dynamic-fields').forEach(f => f.classList.remove('show'));
    document.getElementById('fields-' + type).classList.add('show');
}

let episodeCount = 0;
function addEpisodeRow() {
    episodeCount++;
    const div = document.createElement('div');
    div.className = 'episode-row';
    div.innerHTML = `<span class="ep-num">E1</span><input type="text" placeholder="480p" class="ep-480"><input type="text" placeholder="720p" class="ep-720"><input type="text" placeholder="1080p" class="ep-1080"><button class="btn btn-sm btn-danger" onclick="this.parentElement.remove();renumberEpisodes()">✕</button>`;
    document.getElementById('episodeRows').appendChild(div);
    renumberEpisodes();
}
function renumberEpisodes() {
    const start = parseInt(document.getElementById('epStart').value) || 1;
    document.querySelectorAll('#episodeRows .episode-row').forEach((row, i) => {
        row.querySelector('.ep-num').textContent = 'E' + (start + i);
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

async function doLogin() {
    const id = document.getElementById('loginId').value.trim();
    const pass = document.getElementById('loginPass').value.trim();
    if (!id || !pass) return showToast('Enter credentials', 'error');
    try {
        const r = await fetch(API+'/api/admin-login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({adminId:id,adminPassword:pass})});
        const d = await r.json();
        if (d.success) {
            currentAdminId = id;
            currentAdminName = d.displayName || id;
            const badgeText = d.displayName ? `ADMIN, ${d.displayName}` : 'ADMIN';
            document.getElementById('roleBadge').textContent = badgeText;
            document.getElementById('loginScreen').style.display = 'none';
            document.getElementById('dashboard').style.display = 'block';
            localStorage.setItem('mz_admin_logged','1');
            localStorage.setItem('mz_admin_id', id);
            localStorage.setItem('mz_admin_name', d.displayName || '');
            loadMyStats();
            showToast('Welcome!');
        } else showToast(d.error || 'Invalid credentials', 'error');
    } catch(e) { showToast('Login failed', 'error'); }
}
function doLogout() {
    localStorage.removeItem('mz_admin_logged');
    localStorage.removeItem('mz_admin_id');
    localStorage.removeItem('mz_admin_name');
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('loginScreen').style.display = 'flex';
}
if (localStorage.getItem('mz_admin_logged')) {
    currentAdminId = localStorage.getItem('mz_admin_id') || '';
    currentAdminName = localStorage.getItem('mz_admin_name') || '';
    const badge = currentAdminName ? `ADMIN, ${currentAdminName}` : 'ADMIN';
    document.getElementById('roleBadge').textContent = badge;
    document.getElementById('loginScreen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    loadMyStats();
}

// Stats (only this admin's movies)
async function loadMyStats() {
    try {
        const r = await fetch(API+'/api/movie-links?all=true');
        const movies = await r.json();
        const displayName = currentAdminName || currentAdminId;
        const myMovies = (Array.isArray(movies) ? movies : []).filter(m =>
            m.added_by === currentAdminId || m.added_by === displayName
        );
        document.getElementById('statMovies').textContent = myMovies.length;
        document.getElementById('statViews').textContent = myMovies.reduce((s,m)=>s+(m.views||0),0);
    } catch(e) { console.error(e); }
}

function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

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
}

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
    let body = {
        title, downloadType: type, categories, languages,
        releaseYear, runtime, imdbRating, adsEnabled: true, status: 'pending',
        addedBy: currentAdminName || currentAdminId || 'admin'
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
        const r = await fetch(API+'/api/movie-links', {method:'POST', body: formData});
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
                html = `<div class="link-item"><span>${d.shortUrl || 'Submitted'}</span></div>`;
            }
            container.innerHTML = html;
            document.getElementById('addResult').classList.add('show');
            resetAddForm();
            validateForm();
            showToast('Movie submitted for review!');
            loadMyStats();
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

// MY MOVIES table
let allAdminMovies = [];
async function loadMyMovies() {
    try {
        const r = await fetch(API+'/api/movie-links?all=true');
        const movies = await r.json();
        const displayName = currentAdminName || currentAdminId;
        allAdminMovies = (Array.isArray(movies) ? movies : []).filter(m =>
            m.added_by === currentAdminId || m.added_by === displayName
        );
        const tbody = document.getElementById('myMoviesTable');
        if (!allAdminMovies.length) { tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--text-secondary)">No movies added yet</td></tr>'; return; }
        tbody.innerHTML = allAdminMovies.map(m => {
            const sc = m.status==='approved'?'badge-approved':m.status==='pending'?'badge-pending':'badge-rejected';
            const canEdit = (m.status === 'pending' || m.status === 'rejected');
            const actionBtn = canEdit ? 
                `<button class="btn btn-sm btn-outline" onclick="openEdit(${m.id})">✏️</button> <button class="btn btn-sm btn-danger" onclick="deleteMovie(${m.id})">🗑️</button>` : 
                `<span style="color:var(--text-secondary);font-size:0.8rem">🔒 Locked</span>`;
            return `<tr>
                <td><strong>${esc(m.title||'')}</strong></td>
                <td>${m.download_type||'single'}</td>
                <td><span class="badge ${sc}">${m.status||'pending'}</span></td>
                <td>${m.views||0}</td>
                <td>${(m.created_at||'').slice(0,10)}</td>
                <td><div class="actions" style="display:flex;gap:6px">${actionBtn}</div></td>
            </tr>`;
        }).join('');
    } catch(e) { showToast('Failed','error'); }
}

// Edit Modal functionality
function openEdit(id) {
    const m = allAdminMovies.find(x => x.id === id);
    if (!m) return;
    document.getElementById('editId').value = m.id;
    const dtype = m.download_type || 'single';
    document.getElementById('editType').value = dtype;
    document.getElementById('editTitle').value = m.title||'';

    document.getElementById('editFields-single').style.display = 'none';
    document.getElementById('editFields-quality').style.display = 'none';

    if (dtype === 'single') {
        document.getElementById('editOrigLink').value = m.original_link || '';
        document.getElementById('editFields-single').style.display = 'block';
    } else if (dtype === 'quality' || dtype === 'zip') {
        document.getElementById('editQ480').value = m.quality_480p||'';
        document.getElementById('editQ720').value = m.quality_720p||'';
        document.getElementById('editQ1080').value = m.quality_1080p||'';
        document.getElementById('editFields-quality').style.display = 'block';
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
    const m = allAdminMovies.find(x => x.id === parseInt(id));

    const data = { 
        title: document.getElementById('editTitle').value.trim(),
        categories: getSelectedChips('editCategoriesContainer'),
        languages: getSelectedChips('editLanguagesContainer'),
        release_year: document.getElementById('editYear').value.trim() || 'N/A',
        runtime: document.getElementById('editRuntime').value.trim() || 'N/A',
        imdb_rating: document.getElementById('editImdb').value.trim() || 'N/A',
        ads_enabled: document.getElementById('editAdsToggle').classList.contains('on')
    };
    
    // If the movie was rejected, automatically revert it back to pending for review
    if (m && m.status === 'rejected') {
        data.status = 'pending';
    }

    if (dtype === 'single') {
        data.original_link = document.getElementById('editOrigLink').value.trim();
    } else if (dtype === 'quality' || dtype === 'zip') {
        data.quality_480p = document.getElementById('editQ480').value.trim()||null;
        data.quality_720p = document.getElementById('editQ720').value.trim()||null;
        data.quality_1080p = document.getElementById('editQ1080').value.trim()||null;
    }
    try { await fetch(API+`/api/movie-links/${id}`, {method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}); closeModal(); showToast('Updated!'); loadMyMovies(); } catch(e) { showToast('Failed','error'); }
}

let pendingDeleteId = null;
function deleteMovie(id) {
    const m = allAdminMovies.find(x => x.id === id);
    pendingDeleteId = id;
    document.getElementById('deleteConfirmText').textContent = m ? `"${m.title}" will be permanently deleted.` : 'This movie will be permanently deleted.';
    document.getElementById('deleteConfirmModal').classList.add('show');
    document.getElementById('deleteConfirmYes').onclick = async () => {
        const idToDelete = pendingDeleteId;
        closeDeleteConfirm();
        try { await fetch(API+`/api/movie-links/${idToDelete}`,{method:'DELETE'}); showToast('Deleted'); loadMyMovies(); loadMyStats(); } catch(e) { showToast('Failed','error'); }
    };
}
function closeDeleteConfirm() { document.getElementById('deleteConfirmModal').classList.remove('show'); pendingDeleteId = null; }