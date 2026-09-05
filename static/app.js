// State
let currentUser = null;
let books = [];
let playingBook = null;        // Active audio playback in dock
let inspectedBook = null;      // Currently inspected book in details/enrich modal
let currentChapterIndex = 0;
let sleepTimeout = null;
let sleepInterval = null;
let sleepEndsAt = null;
let lastSyncTime = 0;

// DOM Elements
const audio = document.getElementById("audio-player");
const bookGrid = document.getElementById("book-grid");
const emptyState = document.getElementById("empty-state");
const libraryCount = document.getElementById("library-count");
const pageTitle = document.getElementById("page-title");
const headerSiteName = document.getElementById("header-site-name");

// Search, Filter & Sort Toolbar
const libraryToolbar = document.querySelector(".library-toolbar");
const librarySearch = document.getElementById("library-search");
const btnSearchClear = document.getElementById("btn-search-clear");
const filterChips = document.querySelectorAll(".filter-chip");
const filterChipUploads = document.getElementById("filter-chip-uploads");
const librarySort = document.getElementById("library-sort");
const searchEmptyState = document.getElementById("search-empty-state");
const searchEmptyText = document.getElementById("search-empty-text");
const btnResetFilters = document.getElementById("btn-reset-filters");

let currentSearchQuery = "";
let currentFilter = "all";
let currentSort = "recent";

// Header User Profile, Admin & Upload

const userProfile = document.getElementById("user-profile");
const userDisplayName = document.getElementById("user-display-name");
const userRoleBadge = document.getElementById("user-role-badge");
const btnLogout = document.getElementById("btn-logout");
const btnAdminPanel = document.getElementById("btn-admin-panel");
const btnUpload = document.getElementById("btn-upload");
const btnScan = document.getElementById("btn-scan");

// Floating Player Dock
const playerBar = document.getElementById("player-bar");
const playerCover = document.getElementById("player-cover");
const playerTitle = document.getElementById("player-title");
const playerChapter = document.getElementById("player-chapter");
const playerAuthor = document.getElementById("player-author");
const playerInfoDock = document.getElementById("player-info-dock");

const btnPlay = document.getElementById("btn-play");
const playIcon = document.getElementById("play-icon");
const pauseIcon = document.getElementById("pause-icon");
const btnSkipBack = document.getElementById("btn-skip-back");
const btnSkipForward = document.getElementById("btn-skip-forward");
const btnPrevChap = document.getElementById("btn-prev-chap");
const btnNextChap = document.getElementById("btn-next-chap");
const timeCurrent = document.getElementById("time-current");
const timeTotal = document.getElementById("time-total");
const scrubberContainer = document.getElementById("scrubber-container");
const scrubberFill = document.getElementById("scrubber-fill");
const speedSelect = document.getElementById("speed-select");
const btnSleep = document.getElementById("btn-sleep");
const sleepBadge = document.getElementById("sleep-badge");
const btnPlayerDrawer = document.getElementById("btn-player-drawer");

// Book Details Modal (Decoupled Inspection)
const detailsBackdrop = document.getElementById("details-backdrop");
const detailsClose = document.getElementById("details-close");
const detailsTitle = document.getElementById("details-title");
const detailsAuthor = document.getElementById("details-author");
const detailsCover = document.getElementById("details-cover");
const detailsNarrator = document.getElementById("details-narrator");
const detailsDuration = document.getElementById("details-duration");
const detailsProgressText = document.getElementById("details-progress-text");
const detailsChapterCount = document.getElementById("details-chapter-count");
const detailsChapterList = document.getElementById("details-chapter-list");
const btnDetailsPlay = document.getElementById("btn-details-play");
const btnDetailsPlayText = document.getElementById("btn-details-play-text");
const btnDetailsEnrich = document.getElementById("btn-details-enrich");
const btnDetailsReset = document.getElementById("btn-details-reset");
const btnDetailsDelete = document.getElementById("btn-details-delete");

// Navigation & Views
const navTabLibrary = document.getElementById("nav-tab-library");
const navTabHistory = document.getElementById("nav-tab-history");
const viewLibrary = document.getElementById("view-library");
const viewHistory = document.getElementById("view-history");
const btnHistoryGoLibrary = document.getElementById("btn-history-go-library");

// Stats & History Elements
const statTotalTime = document.getElementById("stat-total-time");
const statCompletedCount = document.getElementById("stat-completed-count");
const statInprogressCount = document.getElementById("stat-inprogress-count");
const statTopAuthor = document.getElementById("stat-top-author");
const historyCount = document.getElementById("history-count");
const historyTimelineList = document.getElementById("history-timeline-list");
const historyEmptyState = document.getElementById("history-empty-state");

let currentView = "library";

// Enrich Chapters Modal
const enrichBackdrop = document.getElementById("enrich-backdrop");
const enrichClose = document.getElementById("enrich-close");
const enrichCancel = document.getElementById("enrich-cancel");
const enrichSave = document.getElementById("enrich-save");
const enrichTextarea = document.getElementById("enrich-textarea");
const enrichStats = document.getElementById("enrich-stats");
const enrichWriteFile = document.getElementById("enrich-write-file");
const enrichBookSubtitle = document.getElementById("enrich-book-subtitle");

// Online Lookup
const lookupQuery = document.getElementById("lookup-query");
const btnLookupSearch = document.getElementById("btn-lookup-search");
const lookupResults = document.getElementById("lookup-results");

// Whisper AI
const btnWhisperTranscribe = document.getElementById("btn-whisper-transcribe");
const whisperProgressContainer = document.getElementById("whisper-progress-container");
const whisperStatusText = document.getElementById("whisper-status-text");
const whisperPctText = document.getElementById("whisper-pct-text");
const whisperProgressFill = document.getElementById("whisper-progress-fill");
let whisperEventSource = null;

// Setup Wizard Modal
const setupBackdrop = document.getElementById("setup-backdrop");
const setupSiteName = document.getElementById("setup-sitename");
const setupPath = document.getElementById("setup-path");
const setupUsername = document.getElementById("setup-username");
const setupPassword = document.getElementById("setup-password");
const btnSetupFinish = document.getElementById("btn-setup-finish");

// Login Modal
const loginBackdrop = document.getElementById("login-backdrop");
const loginUsername = document.getElementById("login-username");
const loginPassword = document.getElementById("login-password");
const btnLoginSubmit = document.getElementById("btn-login-submit");
const loginError = document.getElementById("login-error");

// Admin Modal
const adminBackdrop = document.getElementById("admin-backdrop");
const adminClose = document.getElementById("admin-close");
const adminNewUser = document.getElementById("admin-new-user");
const adminNewPass = document.getElementById("admin-new-pass");
const adminNewRole = document.getElementById("admin-new-role");
const adminNewAccess = document.getElementById("admin-new-access");
const adminNewCanUpload = document.getElementById("admin-new-can-upload");
const btnAdminAddUser = document.getElementById("btn-admin-add-user");
const adminUserList = document.getElementById("admin-user-list");
const adminCfgSitename = document.getElementById("admin-cfg-sitename");
const adminCfgPath = document.getElementById("admin-cfg-path");
const btnAdminSaveCfg = document.getElementById("btn-admin-save-cfg");
const btnAdminRebuildDb = document.getElementById("btn-admin-rebuild-db");
const adminRebuildRescan = document.getElementById("admin-rebuild-rescan");


// Upload Modal
const uploadBackdrop = document.getElementById("upload-backdrop");
const uploadClose = document.getElementById("upload-close");
const uploadCancel = document.getElementById("upload-cancel");
const uploadSubmit = document.getElementById("upload-submit");
const uploadDropzone = document.getElementById("upload-dropzone");
const uploadFileInput = document.getElementById("upload-file-input");
const uploadFileInfo = document.getElementById("upload-file-info");
const uploadFilename = document.getElementById("upload-filename");
const uploadFilesize = document.getElementById("upload-filesize");
const uploadProgressContainer = document.getElementById("upload-progress-container");
const uploadStatusText = document.getElementById("upload-status-text");
const uploadPctText = document.getElementById("upload-pct-text");
const uploadProgressFill = document.getElementById("upload-progress-fill");

// Utilities
function formatTime(seconds) {
  if (isNaN(seconds) || seconds < 0) return "0:00:00";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}

// -------------------------------------------------------------
// APP INITIALIZATION & AUTH CHECKS
// -------------------------------------------------------------
async function initApp() {
  try {
    const res = await fetch("/api/setup/status");
    const status = await res.json();
    
    if (status.site_name) {
      headerSiteName.textContent = status.site_name;
      pageTitle.textContent = status.site_name;
    }

    if (status.setup_required) {
      setupBackdrop.classList.add("open");
      return;
    }

    // Check login session
    const meRes = await fetch("/api/auth/me");
    if (meRes.ok) {
      const meData = await meRes.json();
      setCurrentUser(meData.user);
      loadLibrary();
    } else {
      loginBackdrop.classList.add("open");
    }
  } catch (err) {
    console.error("Initialization error:", err);
  }
}

function setCurrentUser(user) {
  currentUser = user;
  if (!user) {
    userProfile.style.display = "none";
    btnAdminPanel.style.display = "none";
    if (btnUpload) btnUpload.style.display = "none";
    return;
  }

  userDisplayName.textContent = user.username;
  userRoleBadge.textContent = user.role;
  if (user.role !== "admin" && !user.shared_library) {
    userRoleBadge.textContent = "Personal";
    userRoleBadge.title = "Personal Library Access Only";
  }
  userProfile.style.display = "flex";
  
  if (user.role === "admin") {
    btnAdminPanel.style.display = "inline-flex";
  } else {
    btnAdminPanel.style.display = "none";
  }

  if (btnUpload) {
    if (user.can_upload || user.role === "admin") {
      btnUpload.style.display = "inline-flex";
    } else {
      btnUpload.style.display = "none";
    }
  }
}

// Setup Wizard Finish
if (btnSetupFinish) {
  btnSetupFinish.addEventListener("click", async () => {
    const sitename = setupSiteName.value.trim();
    const path = setupPath.value.trim();
    const username = setupUsername.value.trim();
    const password = setupPassword.value;

    if (!sitename || !path || !username || !password) {
      alert("Please fill in all fields.");
      return;
    }

    btnSetupFinish.disabled = true;
    btnSetupFinish.textContent = "Setting up server...";

    try {
      const res = await fetch("/api/setup/initialize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          site_name: sitename,
          audiobooks_dir: path,
          admin_username: username,
          admin_password: password
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Setup failed");

      setupBackdrop.classList.remove("open");
      headerSiteName.textContent = data.config.site_name;
      pageTitle.textContent = data.config.site_name;
      setCurrentUser(data.user);
      loadLibrary();
    } catch (err) {
      alert("Setup error: " + err.message);
    } finally {
      btnSetupFinish.disabled = false;
      btnSetupFinish.textContent = "Complete Setup & Launch Library";
    }
  });
}

// Login Submit
if (btnLoginSubmit) {
  btnLoginSubmit.addEventListener("click", async () => {
    const username = loginUsername.value.trim();
    const password = loginPassword.value;
    loginError.style.display = "none";

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Login failed");

      loginBackdrop.classList.remove("open");
      setCurrentUser(data.user);
      loadLibrary();
    } catch (err) {
      loginError.textContent = err.message;
      loginError.style.display = "block";
    }
  });
}

// Logout
if (btnLogout) {
  btnLogout.addEventListener("click", async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.reload();
  });
}

// -------------------------------------------------------------
// LIBRARY LOADING & RENDERING
// -------------------------------------------------------------
async function loadLibrary() {
  try {
    const res = await fetch("/api/books");
    if (res.status === 401) {
      loginBackdrop.classList.add("open");
      return;
    }
    const data = await res.json();
    books = data.books || [];
    libraryCount.textContent = `${books.length} book${books.length === 1 ? "" : "s"}`;
    renderLibrary();
  } catch (err) {
    console.error("Failed loading library:", err);
  }
}

function getFilteredAndSortedBooks() {
  let result = [...books];

  // 1. Status Filter (In Progress requires at least 2 minutes / 120s of listening)
  if (currentFilter === "in-progress") {
    result = result.filter(b => b.progress && (b.progress.position || 0) >= 120 && !b.progress.completed);
  } else if (currentFilter === "unheard") {
    result = result.filter(b => !b.progress || ((b.progress.position || 0) < 120 && !b.progress.completed));
  } else if (currentFilter === "completed") {
    result = result.filter(b => b.progress && b.progress.completed);
  } else if (currentFilter === "uploads") {
    if (currentUser) {
      result = result.filter(b => b.uploaded_by === currentUser.id);
    }
  }

  // 2. Text Search Query
  if (currentSearchQuery) {
    const q = currentSearchQuery.toLowerCase();
    result = result.filter(b => {
      const title = (b.title || "").toLowerCase();
      const author = (b.author || "").toLowerCase();
      const narrator = (b.narrator || "").toLowerCase();
      const desc = (b.description || "").toLowerCase();
      return title.includes(q) || author.includes(q) || narrator.includes(q) || desc.includes(q);
    });
  }

  // 3. Sorting
  if (currentSort === "title-asc") {
    result.sort((a, b) => (a.title || "").localeCompare(b.title || ""));
  } else if (currentSort === "title-desc") {
    result.sort((a, b) => (b.title || "").localeCompare(a.title || ""));
  } else if (currentSort === "author-asc") {
    result.sort((a, b) => (a.author || "Unknown").localeCompare(b.author || "Unknown"));
  } else if (currentSort === "duration-desc") {
    result.sort((a, b) => (b.duration || 0) - (a.duration || 0));
  } else if (currentSort === "duration-asc") {
    result.sort((a, b) => (a.duration || 0) - (b.duration || 0));
  }
  // 'recent' uses the default DB order (last_played_at / updated_at DESC)

  return result;
}

function renderLibrary() {
  bookGrid.innerHTML = "";
  if (books.length === 0) {
    if (libraryToolbar) libraryToolbar.style.display = "none";
    if (searchEmptyState) searchEmptyState.style.display = "none";
    emptyState.style.display = "block";
    const h3 = emptyState.querySelector("h3");
    const p = emptyState.querySelector("p");
    if (currentUser && !currentUser.shared_library && currentUser.role !== "admin") {
      if (h3) h3.textContent = "Your Personal Library is Empty";
      if (p) {
        if (currentUser.can_upload) {
          p.innerHTML = "You have personal library access. Click <b>Upload</b> above to add your first audiobook!";
        } else {
          p.innerHTML = "You have personal library access. Contact an administrator to grant upload permissions.";
        }
      }
    } else {
      if (h3) h3.textContent = "No audiobooks found";
      if (p) p.innerHTML = "Place your <code>.m4b</code> files in your configured audiobooks folder and click Rescan, or click Upload above.";
    }
    libraryCount.textContent = "0 books";
    return;
  }
  emptyState.style.display = "none";
  if (libraryToolbar) libraryToolbar.style.display = "flex";

  // Check if current user has any uploaded books
  if (filterChipUploads) {
    const hasUploads = currentUser && books.some(b => b.uploaded_by === currentUser.id);
    filterChipUploads.style.display = hasUploads ? "inline-block" : "none";
  }

  const filteredBooks = getFilteredAndSortedBooks();

  // Dynamic Counter
  if (currentSearchQuery || currentFilter !== "all") {
    libraryCount.textContent = `Showing ${filteredBooks.length} of ${books.length} book${books.length === 1 ? "" : "s"}`;
  } else {
    libraryCount.textContent = `${books.length} book${books.length === 1 ? "" : "s"}`;
  }

  // Handle Search / Filter Empty State
  if (filteredBooks.length === 0) {
    bookGrid.style.display = "none";
    if (searchEmptyState) {
      searchEmptyState.style.display = "block";
      if (searchEmptyText) {
        if (currentSearchQuery) {
          searchEmptyText.textContent = `No audiobooks match "${currentSearchQuery}".`;
        } else {
          searchEmptyText.textContent = `No audiobooks match the "${currentFilter}" filter.`;
        }
      }
    }
    return;
  }

  bookGrid.style.display = "grid";
  if (searchEmptyState) searchEmptyState.style.display = "none";

  filteredBooks.forEach(book => {
    const card = document.createElement("div");
    card.className = `book-card ${playingBook && playingBook.id === book.id ? "active" : ""}`;
    card.id = `card-${book.id}`;
    
    const progressPct = book.duration > 0 ? Math.min(100, (book.progress.position / book.duration) * 100) : 0;
    const coverSrc = book.cover_url || "/api/books/cover";

    card.innerHTML = `
      <div class="card-cover">
        <img src="${coverSrc}" alt="${escapeHtml(book.title)}" loading="lazy">
        <div class="card-play-overlay">
          <div class="card-play-btn" title="Quick Play">
            <svg viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
          </div>
        </div>
        <div class="card-progress-bar">
          <div class="card-progress-fill" style="width: ${progressPct}%"></div>
        </div>
      </div>
      <div class="card-content">
        <div class="card-title" title="${escapeHtml(book.title)}">${escapeHtml(book.title)}</div>
        <div class="card-author">${escapeHtml(book.author || "Unknown")}</div>
        <div class="card-meta">
          <span>${formatTime(book.duration)}</span>
          <span>${Math.round(progressPct)}%</span>
        </div>
      </div>
    `;

    // Click on Card -> OPEN DETAILS (Decoupled, does not auto-play or interrupt audio!)
    card.addEventListener("click", (e) => {
      // If user clicked directly on the play button overlay, start playing directly
      if (e.target.closest(".card-play-overlay")) {
        startPlayingBook(book.id);
      } else {
        openBookDetails(book.id);
      }
    });

    bookGrid.appendChild(card);
  });
}


// -------------------------------------------------------------
// DECOUPLED BOOK DETAILS MODAL
// -------------------------------------------------------------
async function openBookDetails(bookId) {
  try {
    const res = await fetch(`/api/books/${bookId}`);
    if (!res.ok) return;
    const book = await res.json();
    inspectedBook = book;

    detailsTitle.textContent = book.title;
    detailsAuthor.textContent = book.author || "Unknown Author";
    detailsCover.src = book.cover_url || "/api/books/cover";
    detailsNarrator.textContent = book.narrator ? `Narrated by: ${book.narrator}` : "Narrator: -";
    detailsDuration.textContent = `Duration: ${formatTime(book.duration)}`;
    
    const pos = book.progress?.position || 0;
    const pct = book.duration > 0 ? Math.round((pos / book.duration) * 100) : 0;
    detailsProgressText.textContent = `Your Progress: ${pct}% (${formatTime(pos)} of ${formatTime(book.duration)})`;

    if (pos > 0) {
      btnDetailsPlayText.textContent = `Resume from ${formatTime(pos)}`;
    } else {
      btnDetailsPlayText.textContent = "Play Audiobook";
    }

    // Reset Progress button visibility
    if (btnDetailsReset) {
      if (pos > 0) {
        btnDetailsReset.style.display = "inline-flex";
      } else {
        btnDetailsReset.style.display = "none";
      }
    }

    // Delete Audiobook button visibility (uploader or admin)
    if (btnDetailsDelete) {
      const canDelete = currentUser && (currentUser.role === "admin" || (book.uploaded_by && book.uploaded_by === currentUser.id));
      if (canDelete) {
        btnDetailsDelete.style.display = "inline-flex";
      } else {
        btnDetailsDelete.style.display = "none";
      }
    }

    // Render chapters list inside details
    detailsChapterCount.textContent = (book.chapters || []).length;
    detailsChapterList.innerHTML = "";
    (book.chapters || []).forEach((c, idx) => {
      const li = document.createElement("li");
      li.className = "chapter-item";
      li.innerHTML = `
        <div class="chapter-name">${escapeHtml(c.title)}</div>
        <div class="chapter-time">${formatTime(c.start)}</div>
      `;
      // Clicking a chapter inside details plays that chapter
      li.addEventListener("click", () => {
        startPlayingBook(book.id, c.start);
        closeBookDetails();
      });
      detailsChapterList.appendChild(li);
    });

    detailsBackdrop.classList.add("open");
  } catch (err) {
    console.error("Failed opening book details:", err);
  }
}

function closeBookDetails() {
  detailsBackdrop.classList.remove("open");
}

if (detailsClose) detailsClose.addEventListener("click", closeBookDetails);
if (detailsBackdrop) detailsBackdrop.addEventListener("click", (e) => {
  if (e.target === detailsBackdrop) closeBookDetails();
});

// "Play Audiobook" from details modal
if (btnDetailsPlay) {
  btnDetailsPlay.addEventListener("click", () => {
    if (inspectedBook) {
      startPlayingBook(inspectedBook.id);
      closeBookDetails();
    }
  });
}

// "Edit / Enrich Chapters" from details modal
if (btnDetailsEnrich) {
  btnDetailsEnrich.addEventListener("click", () => {
    if (inspectedBook) {
      openEnrichModal(inspectedBook);
    }
  });
}

// "Reset Progress" from details modal
if (btnDetailsReset) {
  btnDetailsReset.addEventListener("click", async () => {
    if (!inspectedBook) return;
    if (!confirm(`Are you sure you want to reset your listening progress on "${inspectedBook.title}" back to the beginning?`)) {
      return;
    }
    try {
      const res = await fetch(`/api/books/${inspectedBook.id}/reset-progress`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to reset progress");

      // Update inspected book
      inspectedBook.progress = { position: 0.0, playback_rate: 1.0, completed: false, last_played_at: null };
      
      // Update book in local cache
      const b = books.find(x => x.id === inspectedBook.id);
      if (b) {
        b.progress = { position: 0.0, playback_rate: 1.0, completed: false, last_played_at: null };
      }

      // If playing this book right now, seek to beginning
      if (playingBook && playingBook.id === inspectedBook.id) {
        audio.currentTime = 0;
        timeCurrent.textContent = formatTime(0);
        scrubberFill.style.width = "0%";
      }

      // Update modal text
      detailsProgressText.textContent = `Your Progress: 0% (${formatTime(0)} of ${formatTime(inspectedBook.duration)})`;
      btnDetailsPlayText.textContent = "Play Audiobook";
      btnDetailsReset.style.display = "none";

      renderLibrary();
      if (currentView === "history") {
        loadHistoryAndStats();
      }
    } catch (err) {
      alert("Error resetting progress: " + err.message);
    }
  });
}

// "Delete Audiobook" from details modal
if (btnDetailsDelete) {
  btnDetailsDelete.addEventListener("click", async () => {
    if (!inspectedBook) return;
    if (!confirm(`Are you sure you want to permanently delete "${inspectedBook.title}"? This cannot be undone.`)) {
      return;
    }
    try {
      const res = await fetch(`/api/books/${inspectedBook.id}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to delete audiobook");

      // Stop playback if currently playing
      if (playingBook && playingBook.id === inspectedBook.id) {
        audio.pause();
        audio.src = "";
        playingBook = null;
        playerBar.classList.remove("visible");
        document.body.style.paddingBottom = "0px";
      }

      closeBookDetails();
      await loadLibrary();
      if (currentView === "history") {
        loadHistoryAndStats();
      }
    } catch (err) {
      alert("Error deleting audiobook: " + err.message);
    }
  });
}

// -------------------------------------------------------------
// VIEW SWITCHING (LIBRARY vs HISTORY & STATS)
// -------------------------------------------------------------
function switchView(viewName) {
  currentView = viewName;
  if (viewName === "library") {
    if (navTabLibrary) navTabLibrary.classList.add("active");
    if (navTabHistory) navTabHistory.classList.remove("active");
    if (viewLibrary) viewLibrary.style.display = "block";
    if (viewHistory) viewHistory.style.display = "none";
  } else if (viewName === "history") {
    if (navTabLibrary) navTabLibrary.classList.remove("active");
    if (navTabHistory) navTabHistory.classList.add("active");
    if (viewLibrary) viewLibrary.style.display = "none";
    if (viewHistory) viewHistory.style.display = "block";
    loadHistoryAndStats();
  }
}

if (navTabLibrary) navTabLibrary.addEventListener("click", () => switchView("library"));
if (navTabHistory) navTabHistory.addEventListener("click", () => switchView("history"));
if (btnHistoryGoLibrary) btnHistoryGoLibrary.addEventListener("click", () => switchView("library"));

// -------------------------------------------------------------
// USER LISTENING HISTORY & STATISTICS
// -------------------------------------------------------------
function formatListeningDuration(seconds) {
  if (!seconds || seconds <= 0) return "0m";
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  let parts = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0 || parts.length === 0) parts.push(`${minutes}m`);
  return parts.join(" ");
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return "Recently";
  const d = new Date(dateStr.endsWith("Z") ? dateStr : dateStr + "Z");
  if (isNaN(d.getTime())) return dateStr;
  
  const now = new Date();
  const diffSec = Math.floor((now - d) / 1000);
  
  if (diffSec < 60) return "Just now";
  if (diffSec < 3600) return `${Math.max(1, Math.floor(diffSec / 60))}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  if (diffSec < 172800) return "Yesterday";
  if (diffSec < 604800) return `${Math.floor(diffSec / 86400)}d ago`;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: d.getFullYear() !== now.getFullYear() ? "numeric" : undefined });
}

async function loadHistoryAndStats() {
  try {
    const res = await fetch("/api/user/history");
    if (!res.ok) return;
    const data = await res.json();
    const stats = data.stats || {};
    const items = data.history || [];

    // Populate Stat Cards
    if (statTotalTime) statTotalTime.textContent = formatListeningDuration(stats.total_listen_seconds || 0);
    if (statCompletedCount) statCompletedCount.textContent = stats.completed_count || 0;
    if (statInprogressCount) statInprogressCount.textContent = stats.in_progress_count || 0;
    if (statTopAuthor) statTopAuthor.textContent = stats.top_author || "-";
    if (historyCount) historyCount.textContent = `${items.length} audiobook${items.length === 1 ? "" : "s"}`;

    // Render Timeline List
    if (!historyTimelineList) return;
    historyTimelineList.innerHTML = "";

    if (items.length === 0) {
      if (historyEmptyState) historyEmptyState.style.display = "block";
      historyTimelineList.style.display = "none";
      return;
    }

    if (historyEmptyState) historyEmptyState.style.display = "none";
    historyTimelineList.style.display = "flex";

    items.forEach(item => {
      const el = document.createElement("div");
      el.className = "history-item";
      
      const pct = item.duration > 0 ? Math.min(100, Math.round((item.position / item.duration) * 100)) : 0;
      const coverSrc = item.cover_url || "/api/books/cover";
      const relTime = formatRelativeTime(item.last_played_at);
      
      el.innerHTML = `
        <div class="history-top-row" style="display: flex; align-items: center; gap: 14px; flex: 1; min-width: 0;">
          <div class="history-cover-wrap">
            <img src="${coverSrc}" alt="${escapeHtml(item.title)}" loading="lazy">
          </div>
          <div class="history-details">
            <div class="history-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</div>
            <div class="history-meta">
              <span>${escapeHtml(item.author || "Unknown")}</span>
              <span>&bull;</span>
              <span>${formatTime(item.duration)}</span>
              <span>&bull;</span>
              <span style="color: var(--accent); font-weight: 500;">${relTime}</span>
            </div>
            <div class="history-progress-wrap">
              <div class="history-progress-bar">
                <div class="history-progress-fill" style="width: ${pct}%;"></div>
              </div>
              <span class="history-progress-text">${pct}% (${formatTime(item.position)})</span>
            </div>
          </div>
        </div>
        <div class="history-actions">
          <button class="btn-history-play" title="Play / Resume">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
            <span>${item.position > 0 && !item.completed ? "Resume" : "Play"}</span>
          </button>
          <button class="btn-history-reset" title="Reset your listening progress">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path><path d="M3 3v5h5"></path></svg>
            <span>Reset</span>
          </button>
        </div>
      `;

      // Play button
      const playBtn = el.querySelector(".btn-history-play");
      playBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        startPlayingBook(item.book_id, item.position > 0 && !item.completed ? item.position : 0);
      });

      // Reset progress button
      const resetBtn = el.querySelector(".btn-history-reset");
      resetBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        if (!confirm(`Are you sure you want to reset your progress for "${item.title}" back to 0:00?`)) return;
        try {
          const res = await fetch(`/api/books/${item.book_id}/reset-progress`, { method: "POST" });
          if (!res.ok) throw new Error("Failed to reset progress");
          
          const b = books.find(x => x.id === item.book_id);
          if (b) {
            b.progress = { position: 0.0, playback_rate: 1.0, completed: false, last_played_at: null };
          }
          if (playingBook && playingBook.id === item.book_id) {
            audio.currentTime = 0;
            timeCurrent.textContent = formatTime(0);
            scrubberFill.style.width = "0%";
          }
          loadHistoryAndStats();
          renderLibrary();
        } catch (err) {
          alert("Error resetting progress: " + err.message);
        }
      });

      // Clicking row opens book details modal
      el.addEventListener("click", () => {
        openBookDetails(item.book_id);
      });

      historyTimelineList.appendChild(el);
    });
  } catch (err) {
    console.error("Failed loading history & stats:", err);
  }
}

// -------------------------------------------------------------
// AUDIO PLAYBACK CONTROLS (INDEPENDENT DOCK)
// -------------------------------------------------------------
async function startPlayingBook(bookId, startAt = null) {
  try {
    const res = await fetch(`/api/books/${bookId}`);
    if (!res.ok) return;
    const book = await res.json();
    playingBook = book;

    // Card highlight
    document.querySelectorAll(".book-card").forEach(c => c.classList.remove("active"));
    const activeCard = document.getElementById(`card-${bookId}`);
    if (activeCard) activeCard.classList.add("active");

    playerTitle.textContent = book.title;
    playerAuthor.textContent = book.author || "Unknown Author";
    playerCover.src = book.cover_url || "/api/books/cover";
    playerBar.classList.add("visible");

    const streamUrl = `/api/books/${book.id}/stream`;
    audio.src = streamUrl;
    audio.playbackRate = parseFloat(speedSelect.value) || 1.0;

    const resumePos = startAt !== null ? startAt : (book.progress?.position || 0);

    audio.addEventListener("loadedmetadata", () => {
      if (resumePos > 0 && resumePos < audio.duration) {
        audio.currentTime = resumePos;
      }
      updateTimeUI();
      audio.play();
    }, { once: true });

    setupMediaSession();
  } catch (err) {
    console.error("Playback start error:", err);
  }
}

function updateActiveChapter(currentTime, force = false) {
  if (!playingBook || !playingBook.chapters || playingBook.chapters.length === 0) {
    playerChapter.textContent = playingBook?.title || "";
    return;
  }

  const chaps = playingBook.chapters;
  let activeIdx = 0;
  for (let i = 0; i < chaps.length; i++) {
    if (currentTime >= chaps[i].start) {
      activeIdx = i;
    } else {
      break;
    }
  }

  const targetTitle = chaps[activeIdx]?.title || `Chapter ${activeIdx + 1}`;
  if (force || activeIdx !== currentChapterIndex || playerChapter.textContent !== targetTitle) {
    currentChapterIndex = activeIdx;
    playerChapter.textContent = targetTitle;
  }
}

// Save progress for current user
async function syncProgress(force = false) {
  if (!playingBook || !currentUser) return;
  const now = Date.now();
  if (!force && now - lastSyncTime < 4000) return;
  lastSyncTime = now;

  const pos = audio.currentTime;
  const duration = audio.duration || playingBook.duration || 1;
  const isCompleted = pos >= duration - 10;

  try {
    await fetch(`/api/books/${playingBook.id}/progress`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        position: pos,
        playback_rate: audio.playbackRate,
        completed: isCompleted
      }),
      keepalive: true
    });

    const card = document.getElementById(`card-${playingBook.id}`);
    if (card) {
      const fill = card.querySelector(".card-progress-fill");
      if (fill) fill.style.width = `${Math.min(100, (pos / duration) * 100)}%`;
    }

    // Keep memory cache updated
    const bookInList = books.find(b => b.id === playingBook.id);
    if (bookInList) {
      bookInList.progress = {
        position: pos,
        playback_rate: audio.playbackRate,
        completed: isCompleted,
        last_played_at: new Date().toISOString()
      };
    }
    if (currentView === "history") {
      loadHistoryAndStats();
    }
  } catch (err) {
    console.warn("Progress sync error:", err);
  }
}

function setupMediaSession() {
  if (!("mediaSession" in navigator) || !playingBook) return;

  navigator.mediaSession.metadata = new MediaMetadata({
    title: playingBook.title,
    artist: playingBook.author || "Audiobook",
    album: playingBook.narrator ? `Narrated by ${playingBook.narrator}` : "Audiobook",
    artwork: [{ src: playingBook.cover_url || "/api/books/cover", sizes: "512x512", type: "image/jpeg" }]
  });

  navigator.mediaSession.setActionHandler("play", () => audio.play());
  navigator.mediaSession.setActionHandler("pause", () => audio.pause());
  navigator.mediaSession.setActionHandler("seekbackward", (details) => {
    const skip = details.seekOffset || 15;
    audio.currentTime = Math.max(0, audio.currentTime - skip);
  });
  navigator.mediaSession.setActionHandler("seekforward", (details) => {
    const skip = details.seekOffset || 30;
    audio.currentTime = Math.min(audio.duration, audio.currentTime + skip);
  });
}

// Audio events
audio.addEventListener("play", () => {
  playIcon.style.display = "none";
  pauseIcon.style.display = "block";
  if ("mediaSession" in navigator) navigator.mediaSession.playbackState = "playing";
});

audio.addEventListener("pause", () => {
  playIcon.style.display = "block";
  pauseIcon.style.display = "none";
  if ("mediaSession" in navigator) navigator.mediaSession.playbackState = "paused";
  syncProgress(true);
});

audio.addEventListener("timeupdate", () => {
  updateTimeUI();
  updateActiveChapter(audio.currentTime);
  syncProgress(false);
});

function updateTimeUI() {
  const current = audio.currentTime || 0;
  const total = audio.duration || (playingBook ? playingBook.duration : 0);
  timeCurrent.textContent = formatTime(current);
  timeTotal.textContent = formatTime(total);
  if (total > 0) {
    scrubberFill.style.width = `${(current / total) * 100}%`;
  }
}

// Scrubber Click & Touch Scrubbing
function handleScrubberSeek(clientX) {
  const rect = scrubberContainer.getBoundingClientRect();
  const clickX = clientX - rect.left;
  const pct = Math.max(0, Math.min(1, clickX / rect.width));
  const total = audio.duration || (playingBook ? playingBook.duration : 0);
  if (total > 0) {
    audio.currentTime = pct * total;
    scrubberFill.style.width = `${pct * 100}%`;
    timeCurrent.textContent = formatTime(audio.currentTime);
    syncProgress(true);
  }
}

scrubberContainer.addEventListener("click", (e) => handleScrubberSeek(e.clientX));

let isScrubbingTouch = false;
scrubberContainer.addEventListener("touchstart", (e) => {
  isScrubbingTouch = true;
  if (e.touches && e.touches.length > 0) {
    handleScrubberSeek(e.touches[0].clientX);
  }
}, { passive: true });

window.addEventListener("touchmove", (e) => {
  if (!isScrubbingTouch) return;
  if (e.touches && e.touches.length > 0) {
    handleScrubberSeek(e.touches[0].clientX);
  }
}, { passive: true });

window.addEventListener("touchend", () => {
  if (isScrubbingTouch) {
    isScrubbingTouch = false;
    syncProgress(true);
  }
});


btnPlay.addEventListener("click", () => {
  if (audio.paused) audio.play();
  else audio.pause();
});

btnSkipBack.addEventListener("click", () => {
  audio.currentTime = Math.max(0, audio.currentTime - 15);
  syncProgress(true);
});

btnSkipForward.addEventListener("click", () => {
  audio.currentTime = Math.min(audio.duration || Infinity, audio.currentTime + 30);
  syncProgress(true);
});

btnPrevChap.addEventListener("click", () => jumpPlayingChapter(-1));
btnNextChap.addEventListener("click", () => jumpPlayingChapter(1));

function jumpPlayingChapter(direction) {
  if (!playingBook || !playingBook.chapters || playingBook.chapters.length === 0) return;
  const targetIdx = currentChapterIndex + direction;
  if (targetIdx >= 0 && targetIdx < playingBook.chapters.length) {
    audio.currentTime = playingBook.chapters[targetIdx].start;
  }
}

// Clicking the player dock info opens details for the playing book
if (playerInfoDock) {
  playerInfoDock.addEventListener("click", () => {
    if (playingBook) openBookDetails(playingBook.id);
  });
}

if (btnPlayerDrawer) {
  btnPlayerDrawer.addEventListener("click", () => {
    if (playingBook) openBookDetails(playingBook.id);
  });
}

speedSelect.addEventListener("change", (e) => {
  audio.playbackRate = parseFloat(e.target.value);
  syncProgress(true);
});

// Sleep Timer
btnSleep.addEventListener("click", () => {
  const choice = prompt("Set Sleep Timer:\n1: 15 min\n2: 30 min\n3: 45 min\n4: 60 min\n0: Off");
  if (choice === null) return;
  clearTimeout(sleepTimeout);
  clearInterval(sleepInterval);
  sleepBadge.style.display = "none";

  const map = { "1": 15, "2": 30, "3": 45, "4": 60 };
  if (map[choice]) {
    const mins = map[choice];
    const ms = mins * 60 * 1000;
    sleepEndsAt = Date.now() + ms;
    sleepBadge.style.display = "inline-block";
    sleepBadge.textContent = `${mins}m`;

    sleepTimeout = setTimeout(() => {
      audio.pause();
      sleepBadge.style.display = "none";
      alert("Sleep timer ended. Audio paused.");
    }, ms);
  }
});

// -------------------------------------------------------------
// ENRICH CHAPTERS (Applies to inspectedBook without touching playback)
// -------------------------------------------------------------
function openEnrichModal(book) {
  inspectedBook = book;
  const chaps = book.chapters || [];
  enrichBookSubtitle.textContent = `Enriching: "${book.title}" (${chaps.length} chapters)`;
  enrichStats.textContent = `Book has ${chaps.length} chapter markers detected.`;
  enrichTextarea.value = chaps.map(c => c.title).join("\n");
  
  if (lookupQuery) {
    lookupQuery.value = `${book.title} ${book.author || ""}`.trim();
  }
  if (lookupResults) {
    lookupResults.innerHTML = "";
    lookupResults.style.display = "none";
  }
  if (whisperProgressContainer) {
    whisperProgressContainer.style.display = "none";
  }
  
  enrichBackdrop.classList.add("open");
}

function closeEnrichModal() {
  if (whisperEventSource) {
    whisperEventSource.close();
    whisperEventSource = null;
  }
  enrichBackdrop.classList.remove("open");
}

if (enrichClose) enrichClose.addEventListener("click", closeEnrichModal);
if (enrichCancel) enrichCancel.addEventListener("click", closeEnrichModal);
if (enrichBackdrop) enrichBackdrop.addEventListener("click", (e) => {
  if (e.target === enrichBackdrop) closeEnrichModal();
});

if (enrichTextarea) {
  enrichTextarea.addEventListener("input", () => {
    const lines = enrichTextarea.value.split("\n").filter(l => l.trim().length > 0);
    const targetCount = inspectedBook ? (inspectedBook.chapters || []).length : 0;
    enrichStats.textContent = `${lines.length} titles provided for ${targetCount} chapter markers.`;
  });
}

// Online Lookup
if (btnLookupSearch) {
  btnLookupSearch.addEventListener("click", async () => {
    const q = lookupQuery.value.trim();
    if (!q) return;

    btnLookupSearch.disabled = true;
    btnLookupSearch.innerHTML = `<span>Searching...</span>`;
    lookupResults.style.display = "block";
    lookupResults.innerHTML = `<div style="font-size:0.8rem; color:var(--text-muted); padding:8px;">Querying Audible & Audnexus...</div>`;

    try {
      const res = await fetch(`/api/lookup/search?query=${encodeURIComponent(q)}`);
      const data = await res.json();
      const results = data.results || [];

      if (results.length === 0) {
        lookupResults.innerHTML = `<div style="font-size:0.8rem; color:var(--text-muted); padding:8px;">No matches found. Try entering the Audible ASIN directly.</div>`;
        return;
      }

      lookupResults.innerHTML = "";
      results.forEach(item => {
        const row = document.createElement("div");
        row.className = "lookup-item";
        row.innerHTML = `
          <div style="overflow:hidden; margin-right:8px;">
            <div class="lookup-item-title">${escapeHtml(item.title)}</div>
            <div class="lookup-item-meta">${escapeHtml(item.author)} &bull; ASIN: ${item.asin}</div>
          </div>
          <button class="btn-use-lookup">Get Chapters</button>
        `;

        row.querySelector(".btn-use-lookup").addEventListener("click", async (e) => {
          e.stopPropagation();
          await fetchAndApplyAsinChapters(item.asin);
        });

        lookupResults.appendChild(row);
      });
    } catch (err) {
      lookupResults.innerHTML = `<div style="font-size:0.8rem; color:#f87171; padding:8px;">Search error: ${err.message}</div>`;
    } finally {
      btnLookupSearch.disabled = false;
      btnLookupSearch.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg><span>Search Online</span>`;
    }
  });
}

async function fetchAndApplyAsinChapters(asin) {
  try {
    const res = await fetch(`/api/lookup/chapters?asin=${encodeURIComponent(asin)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Could not retrieve chapter data from Audnexus");

    const titles = data.titles || [];
    if (titles.length === 0) {
      alert("No chapter titles returned for this book.");
      return;
    }

    enrichTextarea.value = titles.join("\n");
    const targetCount = inspectedBook ? (inspectedBook.chapters || []).length : 0;
    enrichStats.textContent = `Loaded ${titles.length} titles from Audnexus for ${targetCount} chapter markers.`;
    lookupResults.style.display = "none";
  } catch (err) {
    alert("Error fetching chapters: " + err.message);
  }
}

// Whisper Speech-to-Text with Live Progress
if (btnWhisperTranscribe) {
  btnWhisperTranscribe.addEventListener("click", () => {
    if (!inspectedBook) return;

    if (whisperEventSource) {
      whisperEventSource.close();
    }

    btnWhisperTranscribe.disabled = true;
    btnWhisperTranscribe.innerHTML = `<span>Listening with Whisper AI...</span>`;
    
    whisperProgressContainer.style.display = "block";
    whisperStatusText.textContent = "Initializing Whisper AI model...";
    whisperPctText.textContent = "0%";
    whisperProgressFill.style.width = "0%";

    const sseUrl = `/api/books/${inspectedBook.id}/whisper-stream`;
    whisperEventSource = new EventSource(sseUrl);

    whisperEventSource.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data);

        if (event.step === "init" || event.step === "ready") {
          whisperStatusText.textContent = event.message;
        } else if (event.step === "chapter") {
          whisperStatusText.textContent = `Chapter ${event.current} of ${event.total}: "${event.title}"`;
          whisperPctText.textContent = `${event.pct}%`;
          whisperProgressFill.style.width = `${event.pct}%`;
          
          if (event.titles && event.titles.length > 0) {
            enrichTextarea.value = event.titles.join("\n");
            enrichStats.textContent = `Transcribed ${event.current} of ${event.total} chapters (${event.pct}%)...`;
          }
        } else if (event.step === "done") {
          whisperStatusText.textContent = `Finished transcribing ${event.total} chapters! Review above and click "Apply & Save Titles" below to save.`;
          whisperPctText.textContent = "100%";
          whisperProgressFill.style.width = "100%";
          if (event.titles) {
            enrichTextarea.value = event.titles.join("\n");
            enrichStats.textContent = `Whisper finished transcribing ${event.titles.length} chapter titles!`;
          }
          whisperEventSource.close();
          whisperEventSource = null;
          btnWhisperTranscribe.disabled = false;
          btnWhisperTranscribe.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg><span>Listen with Whisper AI</span>`;
        } else if (event.step === "error") {
          alert("Whisper error: " + event.message);
          whisperEventSource.close();
          whisperEventSource = null;
          btnWhisperTranscribe.disabled = false;
        }
      } catch (err) {
        console.error("SSE parse error:", err);
      }
    };

    whisperEventSource.onerror = () => {
      if (whisperEventSource) {
        whisperEventSource.close();
        whisperEventSource = null;
      }
      btnWhisperTranscribe.disabled = false;
      btnWhisperTranscribe.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg><span>Listen with Whisper AI</span>`;
    };
  });
}

// Save Enriched Titles
if (enrichSave) {
  enrichSave.addEventListener("click", async () => {
    if (!inspectedBook) return;
    const lines = enrichTextarea.value.split("\n");
    const writeFile = enrichWriteFile.checked;

    enrichSave.disabled = true;
    enrichSave.textContent = writeFile ? "Remuxing M4B..." : "Saving...";

    try {
      const res = await fetch(`/api/books/${inspectedBook.id}/chapters`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          titles: lines,
          write_to_file: writeFile
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to update chapters");

      inspectedBook.chapters = data.chapters;
      
      // If currently playing book is this book, immediately update player display
      if (playingBook && playingBook.id === inspectedBook.id) {
        playingBook.chapters = data.chapters;
        updateActiveChapter(audio.currentTime, true);
      }

      // Re-render in details modal and refresh library cards
      openBookDetails(inspectedBook.id);
      loadLibrary();
      closeEnrichModal();
      alert(data.message || "Chapters updated successfully!");
    } catch (err) {
      alert("Error saving chapters: " + err.message);
    } finally {
      enrichSave.disabled = false;
      enrichSave.textContent = "Apply & Save Titles";
    }
  });
}

// -------------------------------------------------------------
// ADMIN MANAGEMENT MODAL
// -------------------------------------------------------------
if (btnAdminPanel) {
  btnAdminPanel.addEventListener("click", async () => {
    adminBackdrop.classList.add("open");
    await loadAdminData();
  });
}

if (adminClose) adminClose.addEventListener("click", () => adminBackdrop.classList.remove("open"));
if (adminBackdrop) adminBackdrop.addEventListener("click", (e) => {
  if (e.target === adminBackdrop) adminBackdrop.classList.remove("open");
});

async function loadAdminData() {
  try {
    // Load config
    const cfgRes = await fetch("/api/admin/config");
    if (cfgRes.ok) {
      const cfgData = await cfgRes.json();
      adminCfgSitename.value = cfgData.config.site_name || "";
      adminCfgPath.value = cfgData.config.audiobooks_dir || "";
    }

    // Load users
    const usersRes = await fetch("/api/admin/users");
    if (usersRes.ok) {
      const usersData = await usersRes.json();
      adminUserList.innerHTML = "";
      usersData.users.forEach(u => {
        const row = document.createElement("div");
        row.className = "admin-user-row";
        const libBadge = (u.role === "admin" || u.shared_library)
          ? `<span class="badge-shared" title="Can see shared audiobooks">Shared Lib</span>`
          : `<span class="badge-personal" title="Can only see personal uploads">Personal Only</span>`;
        const uploadBadge = (u.role === "admin" || u.can_upload)
          ? `<span class="badge-upload" title="Uploads allowed">Upload: Yes</span>`
          : `<span style="font-size:0.68rem; color:var(--text-muted); padding:2px 6px; border:1px solid var(--border); border-radius:4px;">Upload: No</span>`;

        row.innerHTML = `
          <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
            <strong>${escapeHtml(u.username)}</strong> 
            <span class="role-pill">${u.role}</span>
            ${libBadge}
            ${uploadBadge}
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            ${u.role !== "admin" ? `
              <button class="btn-icon-subtle" style="font-size:0.75rem; text-decoration:underline; color:var(--accent);" title="Change user library and upload permissions" onclick="editUserPermissions('${u.id}', '${escapeHtml(u.username)}', ${u.shared_library ? 1 : 0}, ${u.can_upload ? 1 : 0})">Permissions</button>
            ` : ""}
            ${u.id !== currentUser.id ? `<button class="btn-icon-subtle" title="Delete User" onclick="deleteUser('${u.id}')" style="font-size:1.1rem; line-height:1;">&times;</button>` : `<span style="color:var(--text-muted);font-size:0.75rem;">(You)</span>`}
          </div>
        `;
        adminUserList.appendChild(row);
      });
    }
  } catch (err) {
    console.error("Admin load error:", err);
  }
}

// Add user
if (btnAdminAddUser) {
  btnAdminAddUser.addEventListener("click", async () => {
    const username = adminNewUser.value.trim();
    const password = adminNewPass.value;
    const role = adminNewRole.value;
    const sharedLibrary = adminNewAccess ? adminNewAccess.value === "shared" : true;
    const canUpload = adminNewCanUpload ? adminNewCanUpload.checked : false;

    if (!username || !password) {
      alert("Username and password required.");
      return;
    }

    try {
      const res = await fetch("/api/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          password,
          role,
          shared_library: sharedLibrary,
          can_upload: canUpload
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to create user");
      
      adminNewUser.value = "";
      adminNewPass.value = "";
      if (adminNewCanUpload) adminNewCanUpload.checked = false;
      await loadAdminData();
    } catch (err) {
      alert("Error adding user: " + err.message);
    }
  });
}

window.editUserPermissions = async function(userId, username, currentShared, currentUpload) {
  const choice = prompt(
    `Set permissions for "${username}":\n` +
    `1: Shared Library + Uploads Allowed\n` +
    `2: Shared Library + Uploads Disabled\n` +
    `3: Personal Only + Uploads Allowed\n` +
    `4: Personal Only + Uploads Disabled`,
    currentShared ? (currentUpload ? "1" : "2") : (currentUpload ? "3" : "4")
  );
  if (!choice) return;

  let newShared = true;
  let newUpload = false;
  if (choice === "1") { newShared = true; newUpload = true; }
  else if (choice === "2") { newShared = true; newUpload = false; }
  else if (choice === "3") { newShared = false; newUpload = true; }
  else if (choice === "4") { newShared = false; newUpload = false; }
  else { alert("Invalid choice."); return; }

  try {
    const res = await fetch(`/api/admin/users/${userId}/permissions`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shared_library: newShared, can_upload: newUpload })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to update permissions");
    }
    await loadAdminData();
  } catch (e) {
    alert("Error updating permissions: " + e.message);
  }
};

window.deleteUser = async function(userId) {
  if (!confirm("Are you sure you want to delete this user?")) return;
  try {
    const res = await fetch(`/api/admin/users/${userId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Delete failed");
    await loadAdminData();
  } catch (err) {
    alert("Error deleting user: " + err.message);
  }
};

// Save Admin Config
if (btnAdminSaveCfg) {
  btnAdminSaveCfg.addEventListener("click", async () => {
    const sitename = adminCfgSitename.value.trim();
    const path = adminCfgPath.value.trim();

    try {
      const res = await fetch("/api/admin/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ site_name: sitename, audiobooks_dir: path })
      });
      const data = await res.json();
      if (!res.ok) throw new Error("Update failed");

      headerSiteName.textContent = data.config.site_name;
      pageTitle.textContent = data.config.site_name;
      alert("Configuration saved successfully!");
    } catch (err) {
      alert("Config save error: " + err.message);
    }
  });
}

// Rebuild Database
if (btnAdminRebuildDb) {
  btnAdminRebuildDb.addEventListener("click", async () => {
    const doRescan = adminRebuildRescan ? adminRebuildRescan.checked : true;
    const msg = doRescan
      ? "Are you sure you want to rebuild the library database?\n\nThis will clear all audiobooks, chapter customizations, listening progress, and cached covers, then rescan your audiobooks directory from scratch.\n\nUser accounts and server settings will NOT be deleted."
      : "Are you sure you want to clear the audiobook database?\n\nThis will clear all audiobooks, chapter customizations, and listening progress.\n\nUser accounts and server settings will NOT be deleted.";

    if (!confirm(msg)) return;

    btnAdminRebuildDb.disabled = true;
    const originalText = btnAdminRebuildDb.textContent;
    btnAdminRebuildDb.textContent = "Rebuilding...";

    try {
      const res = await fetch(`/api/admin/rebuild-db?rescan=${doRescan}`, {
        method: "POST"
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Rebuild failed");

      alert(data.message || "Database successfully rebuilt!");
      adminBackdrop.classList.remove("open");

      // Refresh library display
      setTimeout(() => {
        loadLibrary();
      }, 1000);
    } catch (err) {
      alert("Error rebuilding database: " + err.message);
    } finally {
      btnAdminRebuildDb.disabled = false;
      btnAdminRebuildDb.textContent = originalText;
    }
  });
}


// -------------------------------------------------------------
// AUDIOBOOK UPLOAD MODAL & STREAMING CHUNK UPLOAD
// -------------------------------------------------------------
let selectedUploadFile = null;

function openUploadModal() {
  selectedUploadFile = null;
  if (uploadFileInput) uploadFileInput.value = "";
  if (uploadFileInfo) uploadFileInfo.style.display = "none";
  if (uploadProgressContainer) uploadProgressContainer.style.display = "none";
  if (uploadSubmit) {
    uploadSubmit.disabled = true;
    uploadSubmit.textContent = "Start Upload";
  }
  if (uploadDropzone) uploadDropzone.style.display = "flex";
  uploadBackdrop.classList.add("open");
}

function closeUploadModal() {
  uploadBackdrop.classList.remove("open");
}

if (btnUpload) btnUpload.addEventListener("click", openUploadModal);
if (uploadClose) uploadClose.addEventListener("click", closeUploadModal);
if (uploadCancel) uploadCancel.addEventListener("click", closeUploadModal);
if (uploadBackdrop) {
  uploadBackdrop.addEventListener("click", (e) => {
    if (e.target === uploadBackdrop) closeUploadModal();
  });
}

if (uploadDropzone) {
  uploadDropzone.addEventListener("click", () => {
    if (uploadFileInput) uploadFileInput.click();
  });

  uploadDropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadDropzone.classList.add("dragover");
  });

  uploadDropzone.addEventListener("dragleave", () => {
    uploadDropzone.classList.remove("dragover");
  });

  uploadDropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadDropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleSelectedUploadFile(e.dataTransfer.files[0]);
    }
  });
}

if (uploadFileInput) {
  uploadFileInput.addEventListener("change", () => {
    if (uploadFileInput.files && uploadFileInput.files.length > 0) {
      handleSelectedUploadFile(uploadFileInput.files[0]);
    }
  });
}

function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return "0 MB";
  const mb = bytes / (1024 * 1024);
  if (mb >= 1024) {
    return (mb / 1024).toFixed(2) + " GB";
  }
  return mb.toFixed(1) + " MB";
}

function handleSelectedUploadFile(file) {
  const ext = file.name.split(".").pop().toLowerCase();
  if (!["m4b", "m4a", "mp4"].includes(ext)) {
    alert("Please select an .m4b, .m4a, or .mp4 audiobook file.");
    return;
  }

  selectedUploadFile = file;
  uploadFilename.textContent = file.name;
  uploadFilesize.textContent = formatBytes(file.size);
  uploadFileInfo.style.display = "block";
  uploadSubmit.disabled = false;
}

if (uploadSubmit) {
  uploadSubmit.addEventListener("click", () => {
    if (!selectedUploadFile) return;

    uploadSubmit.disabled = true;
    uploadCancel.disabled = true;
    uploadDropzone.style.display = "none";
    uploadProgressContainer.style.display = "block";
    uploadProgressFill.style.width = "0%";
    uploadPctText.textContent = "0%";
    uploadStatusText.textContent = "Starting upload...";

    const formData = new FormData();
    formData.append("file", selectedUploadFile);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/books/upload", true);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        uploadProgressFill.style.width = `${pct}%`;
        uploadPctText.textContent = `${pct}%`;
        if (pct < 100) {
          uploadStatusText.textContent = `Uploading: ${formatBytes(e.loaded)} / ${formatBytes(e.total)} (${pct}%)`;
        } else {
          uploadStatusText.textContent = "Upload complete! Indexing chapters & artwork...";
        }
      }
    };

    xhr.onload = () => {
      uploadCancel.disabled = false;
      uploadSubmit.disabled = false;
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const resp = JSON.parse(xhr.responseText);
          closeUploadModal();
          alert(resp.message || "Audiobook uploaded successfully!");
          loadLibrary();
        } catch (err) {
          closeUploadModal();
          loadLibrary();
        }
      } else {
        let errMsg = "Upload failed";
        try {
          const errData = JSON.parse(xhr.responseText);
          errMsg = errData.detail || errMsg;
        } catch (e) {}
        alert("Upload error: " + errMsg);
        uploadDropzone.style.display = "flex";
        uploadProgressContainer.style.display = "none";
        uploadSubmit.disabled = false;
      }
    };

    xhr.onerror = () => {
      uploadCancel.disabled = false;
      uploadSubmit.disabled = false;
      uploadDropzone.style.display = "flex";
      uploadProgressContainer.style.display = "none";
      alert("Network error occurred during upload.");
    };

    xhr.send(formData);
  });
}

// Rescan
if (btnScan) {
  btnScan.addEventListener("click", async () => {
    btnScan.textContent = "Scanning...";
    try {
      await fetch("/api/scan", { method: "POST" });
      setTimeout(() => {
        loadLibrary();
        btnScan.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg><span>Rescan</span>`;
      }, 1500);
    } catch (err) {
      alert("Scan failed: " + err);
    }
  });
}

// -------------------------------------------------------------
// SEARCH, FILTER & SORT EVENT LISTENERS
// -------------------------------------------------------------
if (librarySearch) {
  librarySearch.addEventListener("input", () => {
    currentSearchQuery = librarySearch.value.trim();
    if (btnSearchClear) {
      btnSearchClear.style.display = currentSearchQuery ? "block" : "none";
    }
    renderLibrary();
  });

  librarySearch.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      librarySearch.value = "";
      currentSearchQuery = "";
      if (btnSearchClear) btnSearchClear.style.display = "none";
      librarySearch.blur();
      renderLibrary();
    }
  });
}

if (btnSearchClear) {
  btnSearchClear.addEventListener("click", () => {
    librarySearch.value = "";
    currentSearchQuery = "";
    btnSearchClear.style.display = "none";
    librarySearch.focus();
    renderLibrary();
  });
}

if (filterChips) {
  filterChips.forEach(chip => {
    chip.addEventListener("click", () => {
      filterChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      currentFilter = chip.dataset.filter || "all";
      renderLibrary();
    });
  });
}

if (librarySort) {
  librarySort.addEventListener("change", () => {
    currentSort = librarySort.value || "recent";
    renderLibrary();
  });
}

if (btnResetFilters) {
  btnResetFilters.addEventListener("click", () => {
    currentSearchQuery = "";
    currentFilter = "all";
    currentSort = "recent";
    if (librarySearch) librarySearch.value = "";
    if (btnSearchClear) btnSearchClear.style.display = "none";
    if (librarySort) librarySort.value = "recent";
    if (filterChips) {
      filterChips.forEach(c => {
        if (c.dataset.filter === "all") c.classList.add("active");
        else c.classList.remove("active");
      });
    }
    renderLibrary();
  });
}

// Keyboard shortcuts
window.addEventListener("keydown", (e) => {
  if (["input", "textarea", "select"].includes(e.target.tagName.toLowerCase())) return;

  if (e.key === "/") {
    e.preventDefault();
    if (librarySearch) {
      librarySearch.focus();
      librarySearch.select();
    }
    return;
  }

  if (e.code === "Space") {
    e.preventDefault();
    btnPlay.click();
  } else if (e.code === "ArrowLeft") {
    e.preventDefault();
    btnSkipBack.click();

  } else if (e.code === "ArrowRight") {
    e.preventDefault();
    btnSkipForward.click();
  } else if (e.code === "ArrowUp") {
    e.preventDefault();
    audio.volume = Math.min(1, audio.volume + 0.1);
  } else if (e.code === "ArrowDown") {
    e.preventDefault();
    audio.volume = Math.max(0, audio.volume - 0.1);
  }
});

window.addEventListener("beforeunload", () => {
  syncProgress(true);
});

// Run
initApp();

// Register PWA Service Worker
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js").catch((err) => {
      console.warn("[PWA] ServiceWorker registration:", err);
    });
  });
}

