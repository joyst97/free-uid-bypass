/* ==========================================================
   JOYST CORPORATION - CLIENT INTERACTION ENGINE
   ========================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // ───────────────────────────────────────────
    // 1. EVENT EXPIRY & COUNTDOWN LOGIC
    // ───────────────────────────────────────────
    const eventConfig = window.EVENT_CONFIG || { active: true, remSeconds: 259200 };
    const eventBanner = document.getElementById('event-live-banner');
    const eventTimerDigits = document.getElementById('event-timer-digits');
    const whitelistActiveView = document.getElementById('whitelist-active-view');
    const whitelistEndedView = document.getElementById('whitelist-ended-view');

    let eventSecondsRemaining = eventConfig.remSeconds;

    function formatEventTime(totalSec) {
        if (totalSec <= 0) return '0d 0h 0m 0s';
        const d = Math.floor(totalSec / 86400);
        const h = Math.floor((totalSec % 86400) / 3600);
        const m = Math.floor((totalSec % 3600) / 60);
        const s = totalSec % 60;
        return `${d}d ${h}h ${m}m ${s}s`;
    }

    function triggerEventEnded() {
        if (eventBanner) eventBanner.classList.add('hidden');
        if (whitelistActiveView) whitelistActiveView.classList.add('hidden');
        if (whitelistEndedView) whitelistEndedView.classList.remove('hidden');
    }

    if (eventConfig.active && eventSecondsRemaining > 0) {
        if (eventTimerDigits) eventTimerDigits.textContent = formatEventTime(eventSecondsRemaining);
        
        const eventInterval = setInterval(() => {
            eventSecondsRemaining--;
            if (eventSecondsRemaining <= 0) {
                clearInterval(eventInterval);
                triggerEventEnded();
                showToast('Free trial event has ended.', true);
            } else {
                if (eventTimerDigits) eventTimerDigits.textContent = formatEventTime(eventSecondsRemaining);
            }
        }, 1000);
    } else {
        triggerEventEnded();
    }

    // ───────────────────────────────────────────
    // 2. TAB CONTROLLER
    // ───────────────────────────────────────────
    const tabWhitelist = document.getElementById('tab-whitelist');
    const tabStatus = document.getElementById('tab-status');
    const panelWhitelist = document.getElementById('panel-whitelist');
    const panelStatus = document.getElementById('panel-status');

    tabWhitelist.addEventListener('click', () => {
        tabWhitelist.classList.add('active');
        tabStatus.classList.remove('active');
        panelWhitelist.classList.add('active');
        panelStatus.classList.remove('active');
    });

    tabStatus.addEventListener('click', () => {
        tabStatus.classList.add('active');
        tabWhitelist.classList.remove('active');
        panelStatus.classList.add('active');
        panelWhitelist.classList.remove('active');
    });

    // ───────────────────────────────────────────
    // 3. WHITELIST FORM
    // ───────────────────────────────────────────
    const formWhitelist = document.getElementById('form-whitelist');
    const inputUid = document.getElementById('input-uid');
    const btnPaste = document.getElementById('btn-paste');
    const fieldFeedback = document.getElementById('field-feedback');
    const digitCount = document.getElementById('digit-count');
    const btnSubmit = document.getElementById('btn-submit');
    const ctaText = btnSubmit ? btnSubmit.querySelector('.cta-text') : null;
    const spinner = document.getElementById('spinner');

    const cardResult = document.getElementById('card-result');
    const resUid = document.getElementById('res-uid');
    const resExpiry = document.getElementById('res-expiry');
    const btnCopy = document.getElementById('btn-copy');

    let savedUid = '';

    // Real-Time Input Validation
    if (inputUid) {
        inputUid.addEventListener('input', () => {
            const val = inputUid.value.trim();
            const len = val.length;
            digitCount.textContent = `${len} digit${len === 1 ? '' : 's'}`;

            if (len === 0) {
                fieldFeedback.textContent = 'Numbers only • Minimum 7 digits';
                fieldFeedback.style.color = 'var(--text-muted)';
                return;
            }

            if (!/^\d+$/.test(val)) {
                fieldFeedback.textContent = 'Alphabets & symbols are not allowed!';
                fieldFeedback.style.color = 'var(--danger)';
            } else if (len <= 6) {
                fieldFeedback.textContent = `${len}/7 min digits entered`;
                fieldFeedback.style.color = 'var(--text-muted)';
            } else {
                fieldFeedback.textContent = '✓ Ready to whitelist';
                fieldFeedback.style.color = 'var(--emerald)';
            }
        });
    }

    // Paste Action
    if (btnPaste) {
        btnPaste.addEventListener('click', async () => {
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    inputUid.value = text.trim();
                    inputUid.dispatchEvent(new Event('input'));
                    inputUid.focus();
                }
            } catch (err) {
                showToast('Unable to access clipboard.', true);
            }
        });
    }

    // Submit Whitelist
    if (formWhitelist) {
        formWhitelist.addEventListener('submit', async (e) => {
            e.preventDefault();
            const uid = inputUid.value.trim();

            if (!/^\d+$/.test(uid)) {
                showToast('UID must contain numbers only.', true);
                shake(inputUid);
                return;
            }

            if (uid.length <= 6) {
                showToast('UID must be at least 7 digits.', true);
                shake(inputUid);
                return;
            }

            setLoading(true);

            try {
                const res = await fetch('/api/whitelist', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ uid: uid })
                });

                const data = await res.json();
                setLoading(false);

                if (data.event_ended) {
                    triggerEventEnded();
                    showToast(data.message, true);
                    return;
                }

                if (res.ok && data.success) {
                    savedUid = uid;
                    showToast(data.message || 'UID Whitelisted Successfully!');
                    resUid.textContent = data.data.uid;
                    resExpiry.textContent = data.data.expiry_time;
                    cardResult.classList.remove('hidden');
                    cardResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                } else {
                    showToast(data.message || 'Whitelist activation failed.', true);
                    shake(inputUid);
                }

            } catch (err) {
                setLoading(false);
                showToast('Network error connecting to server.', true);
            }
        });
    }

    function setLoading(isLoading) {
        if (!btnSubmit) return;
        btnSubmit.disabled = isLoading;
        if (ctaText) ctaText.style.display = isLoading ? 'none' : 'flex';
        if (spinner) spinner.style.display = isLoading ? 'block' : 'none';
    }

    // Copy UID
    if (btnCopy) {
        btnCopy.addEventListener('click', () => {
            if (savedUid) {
                navigator.clipboard.writeText(savedUid);
                showToast('UID copied to clipboard!');
            }
        });
    }

    // ───────────────────────────────────────────
    // 4. STATUS QUERY
    // ───────────────────────────────────────────
    const inputStatusUid = document.getElementById('input-status-uid');
    const btnCheck = document.getElementById('btn-check');
    const cardStatusResult = document.getElementById('card-status-result');
    const pillStatus = document.getElementById('pill-status');
    const statusResUid = document.getElementById('status-res-uid');
    const timerVal = document.getElementById('timer-val');
    const progressFill = document.getElementById('progress-fill');
    const statusExpiry = document.getElementById('status-expiry');

    let countdownTimer = null;

    if (btnCheck) {
        btnCheck.addEventListener('click', checkStatus);
    }
    if (inputStatusUid) {
        inputStatusUid.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') checkStatus();
        });
    }

    async function checkStatus() {
        const uid = inputStatusUid.value.trim();
        if (!uid) {
            showToast('Enter a UID to check.', true);
            shake(inputStatusUid);
            return;
        }

        btnCheck.disabled = true;
        btnCheck.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

        try {
            const res = await fetch(`/api/status/${encodeURIComponent(uid)}`);
            const data = await res.json();

            btnCheck.disabled = false;
            btnCheck.innerHTML = '<span>Inspect</span><i class="fa-solid fa-arrow-right"></i>';

            if (res.ok && data.success) {
                renderStatusCard(data.data);
            } else {
                cardStatusResult.classList.add('hidden');
                showToast(data.message || 'UID not active on server.', true);
            }
        } catch (err) {
            btnCheck.disabled = false;
            btnCheck.innerHTML = '<span>Inspect</span><i class="fa-solid fa-arrow-right"></i>';
            showToast('Server connection error.', true);
        }
    }

    function renderStatusCard(info) {
        cardStatusResult.classList.remove('hidden');
        statusResUid.textContent = info.uid;
        statusExpiry.textContent = info.expiry_time || '--';

        if (countdownTimer) clearInterval(countdownTimer);

        let rem = info.remaining_seconds || 0;
        updateTimer(rem);

        if (rem > 0) {
            countdownTimer = setInterval(() => {
                rem--;
                if (rem <= 0) {
                    clearInterval(countdownTimer);
                    timerVal.textContent = 'Expired';
                    progressFill.style.width = '0%';
                } else {
                    updateTimer(rem);
                }
            }, 1000);
        }
    }

    function updateTimer(sec) {
        const h = Math.floor(sec / 3600);
        const m = Math.floor((sec % 3600) / 60);
        const s = sec % 60;
        const pad = (n) => String(n).padStart(2, '0');
        timerVal.textContent = `${pad(h)}h : ${pad(m)}m : ${pad(s)}s`;

        const pct = Math.max(0, Math.min(100, Math.floor((sec / 86400) * 100)));
        progressFill.style.width = `${pct}%`;
    }

    // ───────────────────────────────────────────
    // 5. TOAST NOTIFICATION & SHAKE
    // ───────────────────────────────────────────
    const toast = document.getElementById('toast');
    let toastTimeout;

    function showToast(msg, isError = false) {
        if (!toast) return;
        toast.textContent = msg;
        toast.className = `toast show ${isError ? 'error' : ''}`;
        clearTimeout(toastTimeout);
        toastTimeout = setTimeout(() => {
            toast.className = 'toast';
        }, 2800);
    }

    function shake(el) {
        if (!el) return;
        el.classList.add('shake');
        setTimeout(() => el.classList.remove('shake'), 350);
    }
});
