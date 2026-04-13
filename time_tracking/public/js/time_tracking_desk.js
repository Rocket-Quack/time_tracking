frappe.provide("time_tracking.desk");

(() => {
	const SUMMARY_SELECTOR = ".tt-summary";
	const SUMMARY_DIRTY_KEY = "time_tracking.workspace_summary_dirty";
	let refreshTimer = null;
	let refreshInFlight = false;

	function getSummaryRoots() {
		return Array.from(document.querySelectorAll(SUMMARY_SELECTOR));
	}

	function setSummaryDirty(isDirty) {
		try {
			if (isDirty) {
				window.sessionStorage.setItem(SUMMARY_DIRTY_KEY, "1");
			} else {
				window.sessionStorage.removeItem(SUMMARY_DIRTY_KEY);
			}
		} catch (error) {
			// Ignore unavailable storage and continue with in-memory behavior.
		}
	}

	function isSummaryDirty() {
		try {
			return window.sessionStorage.getItem(SUMMARY_DIRTY_KEY) === "1";
		} catch (error) {
			return false;
		}
	}

	function formatMinutes(totalMinutes) {
		const minutes = Math.max(0, Math.round(totalMinutes || 0));
		const hours = Math.floor(minutes / 60);
		const remainder = minutes % 60;
		return `${hours}:${String(remainder).padStart(2, "0")}`;
	}

	function formatSignedMinutes(totalMinutes) {
		const value = Math.round(totalMinutes || 0);
		const sign = value < 0 ? "-" : "";
		return `${sign}${formatMinutes(Math.abs(value))}`;
	}

	function formatVacationDays(value) {
		const rounded = Math.round(Number(value || 0) * 100) / 100;
		return Number.isFinite(rounded) ? rounded.toString() : "0";
	}

	function updateStatus(element, text, tone, hideWhenEmpty) {
		if (!element) {
			return;
		}
		element.textContent = text || "";
		if (hideWhenEmpty) {
			element.style.display = text ? "" : "none";
		} else {
			element.style.display = "";
		}
		if (tone) {
			element.style.color = `var(--tt-summary-${tone})`;
		}
	}

	function updateVacationSummary(root, vacation) {
		const vacationCard = root.querySelector('[data-card="vacation"]');
		const vacationRemaining = root.querySelector('[data-field="vacation-remaining"]');
		const vacationStatus = root.querySelector('[data-field="vacation-status"]');
		if (!vacationCard || !vacationRemaining || !vacationStatus) {
			return;
		}

		vacationCard.style.display = "";
		if (!vacation || !vacation.enabled) {
			vacationRemaining.textContent = "--";
			updateStatus(vacationStatus, __("Vacation is not configured."), "muted");
			return;
		}

		if (!vacation.valid) {
			vacationRemaining.textContent = "--";
			updateStatus(
				vacationStatus,
				vacation.error || __("Vacation balance is unavailable."),
				"negative"
			);
			return;
		}

		const remaining = Number(vacation.remaining_days || 0);
		const used = Number(vacation.used_days || 0);
		const allowance = Number(vacation.allowance_days || 0);

		vacationRemaining.textContent = formatVacationDays(remaining);
		updateStatus(
			vacationStatus,
			__("Used {0} of {1} days.", [formatVacationDays(used), formatVacationDays(allowance)]),
			remaining < 0 ? "negative" : "muted"
		);
	}

	function showProfileMissing(root, message) {
		const weekStatus = root.querySelector('[data-field="week-status"]');
		const monthStatus = root.querySelector('[data-field="month-status"]');
		const weekForecast = root.querySelector('[data-field="week-forecast"]');
		const vacationCard = root.querySelector('[data-card="vacation"]');
		const text = message || __("Time Tracking Profile is required.");

		updateStatus(weekStatus, text, "negative", true);
		updateStatus(monthStatus, "", null, true);
		if (weekForecast) {
			weekForecast.textContent = "0:00";
		}
		if (vacationCard) {
			vacationCard.style.display = "none";
		}
	}

	function updateSummaryRoot(root, data) {
		const weekTotal = root.querySelector('[data-field="week-total"]');
		const weekStatus = root.querySelector('[data-field="week-status"]');
		const monthTotal = root.querySelector('[data-field="month-total"]');
		const monthStatus = root.querySelector('[data-field="month-status"]');
		const weekForecast = root.querySelector('[data-field="week-forecast"]');
		const hoursBalance = root.querySelector('[data-field="hours-balance"]');
		const weeklyMinutes = Number(data.weekly_total_minutes || 0);
		const monthlyMinutes = Number(data.monthly_total_minutes || 0);
		const weeklyForecastMinutes = Number(data.weekly_forecast_minutes || 0);
		const hoursBalanceMinutes = Number(data.hours_balance_minutes || 0);
		const targetPeriod = data.target_period || null;

		if (weekTotal) {
			weekTotal.textContent = formatMinutes(weeklyMinutes);
		}
		if (monthTotal) {
			monthTotal.textContent = formatMinutes(monthlyMinutes);
		}
		if (weekForecast) {
			weekForecast.textContent = formatMinutes(weeklyForecastMinutes);
		}
		if (hoursBalance) {
			hoursBalance.textContent = formatSignedMinutes(hoursBalanceMinutes);
		}

		if (targetPeriod === "Monthly") {
			updateStatus(weekStatus, "", null, true);
		} else if (!data.weekly_target_hours) {
			updateStatus(weekStatus, __("Weekly target not set."), "muted", false);
		} else {
			const diff = weeklyMinutes - Math.round(Number(data.weekly_target_hours) * 60);
			updateStatus(
				weekStatus,
				diff >= 0
					? `${__("Over by")}: ${formatMinutes(diff)}`
					: `${__("Remaining")}: ${formatMinutes(Math.abs(diff))}`,
				diff >= 0 ? "positive" : "negative",
				false
			);
		}

		if (targetPeriod === "Weekly") {
			updateStatus(monthStatus, "", null, true);
		} else if (!data.monthly_target_hours) {
			updateStatus(monthStatus, __("Monthly target not set."), "muted", false);
		} else {
			const diff = monthlyMinutes - Math.round(Number(data.monthly_target_hours) * 60);
			updateStatus(
				monthStatus,
				diff >= 0
					? `${__("Over by")}: ${formatMinutes(diff)}`
					: `${__("Remaining")}: ${formatMinutes(Math.abs(diff))}`,
				diff >= 0 ? "positive" : "negative",
				false
			);
		}

		updateVacationSummary(root, data.vacation);
	}

	function refreshWorkspaceSummary() {
		const roots = getSummaryRoots();
		if (!roots.length || refreshInFlight) {
			return;
		}

		refreshInFlight = true;
		frappe.call({
			method: "time_tracking.time_tracking.workspace_summary.get_workspace_summary",
			callback: function (response) {
				const message = response.message || {};
				roots.forEach((root) => {
					if (message.profile_missing) {
						showProfileMissing(root, message.message);
						return;
					}
					updateSummaryRoot(root, message);
				});
				setSummaryDirty(false);
				refreshInFlight = false;
			},
			error: function () {
				refreshInFlight = false;
			},
		});
	}

	function scheduleSummaryRefresh() {
		if (!isSummaryDirty()) {
			return;
		}
		if (!getSummaryRoots().length) {
			return;
		}
		if (refreshTimer) {
			window.clearTimeout(refreshTimer);
		}
		refreshTimer = window.setTimeout(() => {
			refreshTimer = null;
			refreshWorkspaceSummary();
		}, 120);
	}

	function markSummaryDirty() {
		setSummaryDirty(true);
		scheduleSummaryRefresh();
	}

	window.time_tracking.desk.refreshWorkspaceSummary = refreshWorkspaceSummary;
	window.time_tracking.desk.notifyWorkspaceSummaryChanged = markSummaryDirty;

	window.addEventListener("time-tracking:summary-refresh", markSummaryDirty);

	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", () => {
			scheduleSummaryRefresh();
		});
	}

	if (document.body && window.MutationObserver) {
		const observer = new MutationObserver(() => {
			scheduleSummaryRefresh();
		});
		observer.observe(document.body, { childList: true, subtree: true });
	}
})();
