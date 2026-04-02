import { useState, useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../hooks/useAuth";
import { useDashboard } from "../hooks/useDashboard";
import {
  createPhotosPickerSession,
  pollPhotosPickerSession,
  fetchPhotosPickerMedia,
  patchDashboard,
} from "../api/auth";
import LayoutEditor from "./LayoutEditor";
import styles from "./SettingsPanel.module.css";

function getSavedInterval(dashboard) {
  if (!dashboard?.widget_layout) return 60;
  const photoWidget = dashboard.widget_layout.find((w) => w.widget === "photos");
  return photoWidget?.settings?.interval_seconds ?? 60;
}

function PhotosPicker() {
  const queryClient = useQueryClient();
  const { data: dashboard } = useDashboard();
  const [status, setStatus] = useState("idle");
  const [photoCount, setPhotoCount] = useState(null);
  const [interval, setInterval_] = useState(() => getSavedInterval(dashboard));
  const pollRef = useRef(null);
  const intervalSaveRef = useRef(null);

  const savedSessionId = getSavedPickerSessionId(dashboard);
  const savedPhotoCount = getSavedPhotoCount(dashboard);

  useEffect(() => {
    setInterval_(getSavedInterval(dashboard));
  }, [dashboard]);

  const cleanup = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => cleanup, [cleanup]);

  async function handleChoosePhotos() {
    setStatus("creating");
    try {
      const session = await createPhotosPickerSession();
      const pickerUrl = session.picker_uri.replace(/\/$/, "") + "/autoclose";
      window.open(pickerUrl, "_blank", "noopener");
      setStatus("polling");
      startPolling(session.id);
    } catch {
      setStatus("error");
    }
  }

  function startPolling(sessionId) {
    cleanup();
    pollRef.current = setInterval(async () => {
      try {
        const result = await pollPhotosPickerSession(sessionId);
        if (result.media_items_set) {
          cleanup();
          setStatus("fetching");
          const media = await fetchPhotosPickerMedia(sessionId);
          await savePickerSession(sessionId, media);
          setPhotoCount(media.length);
          setStatus("done");
        }
      } catch {
        cleanup();
        setStatus("error");
      }
    }, 3000);
  }

  async function savePickerSession(sessionId, media) {
    const widgetLayout = dashboard?.widget_layout ?? [];
    const photoWidget = widgetLayout.find((w) => w.widget === "photos");
    const updatedSettings = {
      ...(photoWidget?.settings ?? {}),
      picker_session_id: sessionId,
      cached_media: media,
    };
    const updatedLayout = widgetLayout.map((w) =>
      w.widget === "photos" ? { ...w, settings: updatedSettings } : w
    );
    if (!photoWidget) {
      updatedLayout.push({
        widget: "photos",
        enabled: true,
        position: updatedLayout.length,
        settings: updatedSettings,
      });
    }
    await patchDashboard({ widget_layout: updatedLayout });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  }

  function handleIntervalChange(e) {
    const val = Number(e.target.value);
    setInterval_(val);
    clearTimeout(intervalSaveRef.current);
    intervalSaveRef.current = setTimeout(() => {
      const widgetLayout = dashboard?.widget_layout ?? [];
      const updatedLayout = widgetLayout.map((w) =>
        w.widget === "photos"
          ? { ...w, settings: { ...w.settings, interval_seconds: val } }
          : w
      );
      patchDashboard({ widget_layout: updatedLayout }).then(() => {
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      });
    }, 500);
  }

  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>Background Images</h3>
      {savedSessionId && savedPhotoCount > 0 && status !== "done" && (
        <p className={styles.info}>{savedPhotoCount} photos selected</p>
      )}
      {savedPhotoCount > 1 && (
        <label className={styles.sliderLabel}>
          <span>Rotate every {interval}s</span>
          <input
            type="range"
            min="15"
            max="300"
            step="5"
            value={interval}
            onChange={handleIntervalChange}
            className={styles.slider}
          />
        </label>
      )}
      {status === "idle" && (
        <button
          type="button"
          onClick={handleChoosePhotos}
          className={styles.actionButton}
        >
          Choose Photos
        </button>
      )}
      {status === "creating" && (
        <p className={styles.info}>Opening photo picker...</p>
      )}
      {status === "polling" && (
        <p className={styles.info}>Waiting for photo selection...</p>
      )}
      {status === "fetching" && (
        <p className={styles.info}>Saving photos...</p>
      )}
      {status === "done" && (
        <>
          <p className={styles.success}>{photoCount} photos selected</p>
          <button
            type="button"
            onClick={() => setStatus("idle")}
            className={styles.actionButton}
          >
            Choose Different Photos
          </button>
        </>
      )}
      {status === "error" && (
        <>
          <p className={styles.errorText}>Something went wrong. Please try again.</p>
          <button
            type="button"
            onClick={() => setStatus("idle")}
            className={styles.actionButton}
          >
            Retry
          </button>
        </>
      )}
    </div>
  );
}

function getDexcomSettings(dashboard) {
  if (!dashboard?.widget_layout) return { username: "", password: "", region: "us" };
  const widget = dashboard.widget_layout.find((w) => w.widget === "glucose");
  if (!widget?.settings) return { username: "", password: "", region: "us" };
  return {
    username: widget.settings.dexcom_username || "",
    password: widget.settings.dexcom_password || "",
    region: widget.settings.dexcom_region || "us",
  };
}

function DexcomSettings() {
  const queryClient = useQueryClient();
  const { data: dashboard } = useDashboard();
  const defaults = getDexcomSettings(dashboard);
  const [username, setUsername] = useState(defaults.username);
  const [password, setPassword] = useState(defaults.password);
  const [region, setRegion] = useState(defaults.region);
  const [saved, setSaved] = useState(false);

  async function handleSave() {
    const widgetLayout = dashboard?.widget_layout ?? [];
    const glucoseWidget = widgetLayout.find((w) => w.widget === "glucose");
    const updatedSettings = {
      ...(glucoseWidget?.settings ?? {}),
      dexcom_username: username,
      dexcom_password: password,
      dexcom_region: region,
    };
    const updatedLayout = widgetLayout.map((w) =>
      w.widget === "glucose" ? { ...w, settings: updatedSettings } : w
    );
    if (!glucoseWidget) {
      updatedLayout.push({
        widget: "glucose",
        enabled: true,
        position: updatedLayout.length,
        settings: updatedSettings,
      });
    }
    await patchDashboard({ widget_layout: updatedLayout });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>Dexcom Glucose Monitor</h3>
      <label className={styles.sliderLabel}>
        <span>Username (email or phone)</span>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className={styles.textInput}
          placeholder="email@example.com"
        />
      </label>
      <label className={styles.sliderLabel}>
        <span>Password</span>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={styles.textInput}
        />
      </label>
      <label className={styles.sliderLabel}>
        <span>Region</span>
        <select
          value={region}
          onChange={(e) => setRegion(e.target.value)}
          className={styles.textInput}
        >
          <option value="us">US</option>
          <option value="ous">Outside US</option>
          <option value="jp">Japan</option>
        </select>
      </label>
      {saved && <p className={styles.success}>Saved!</p>}
      <button
        type="button"
        onClick={handleSave}
        className={styles.actionButton}
        disabled={!username || !password}
      >
        Save Dexcom Settings
      </button>
    </div>
  );
}

function getSavedFlashFreq(dashboard) {
  if (!dashboard?.widget_layout) return 4;
  const widget = dashboard.widget_layout.find((w) => w.widget === "photos");
  return widget?.settings?.dashboard_flash_frequency ?? 4;
}

function getSavedFlashDuration(dashboard) {
  if (!dashboard?.widget_layout) return 15;
  const widget = dashboard.widget_layout.find((w) => w.widget === "photos");
  return widget?.settings?.dashboard_flash_seconds ?? 15;
}

function PhotoFrameSection({ photoFrameMode, onToggle, hasPhotos }) {
  const queryClient = useQueryClient();
  const { data: dashboard } = useDashboard();
  const [flashFreq, setFlashFreq] = useState(() => getSavedFlashFreq(dashboard));
  const [flashDuration, setFlashDuration] = useState(() => getSavedFlashDuration(dashboard));
  const freqSaveRef = useRef(null);
  const durSaveRef = useRef(null);

  if (!hasPhotos) return null;

  function savePhotoSetting(key, value) {
    const widgetLayout = dashboard?.widget_layout ?? [];
    const updatedLayout = widgetLayout.map((w) =>
      w.widget === "photos"
        ? { ...w, settings: { ...w.settings, [key]: value } }
        : w
    );
    patchDashboard({ widget_layout: updatedLayout }).then(() => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    });
  }

  function handleFreqChange(e) {
    const val = Number(e.target.value);
    setFlashFreq(val);
    clearTimeout(freqSaveRef.current);
    freqSaveRef.current = setTimeout(() => savePhotoSetting("dashboard_flash_frequency", val), 500);
  }

  function handleDurationChange(e) {
    const val = Number(e.target.value);
    setFlashDuration(val);
    clearTimeout(durSaveRef.current);
    durSaveRef.current = setTimeout(() => savePhotoSetting("dashboard_flash_seconds", val), 500);
  }

  const freqLabel = flashFreq === 0 ? "Never" : `Every ${flashFreq} photos`;

  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>Photo Frame Mode</h3>
      <p className={styles.info}>
        {photoFrameMode
          ? "Dashboard widgets are hidden. Only photos are shown."
          : "Hide all widgets and show only the photo slideshow."}
      </p>
      <button
        type="button"
        onClick={onToggle}
        className={styles.actionButton}
      >
        {photoFrameMode ? "Show Dashboard" : "Enter Photo Frame"}
      </button>
      <label className={styles.sliderLabel}>
        <span>Show dashboard: {freqLabel}</span>
        <input
          type="range"
          min="0"
          max="10"
          step="1"
          value={flashFreq}
          onChange={handleFreqChange}
          className={styles.slider}
        />
      </label>
      {flashFreq > 0 && (
        <label className={styles.sliderLabel}>
          <span>Dashboard visible for {flashDuration}s</span>
          <input
            type="range"
            min="5"
            max="60"
            step="5"
            value={flashDuration}
            onChange={handleDurationChange}
            className={styles.slider}
          />
        </label>
      )}
    </div>
  );
}

const COMMON_TIMEZONES = [
  { value: "Pacific/Honolulu", label: "Hawaii (HST)" },
  { value: "America/Anchorage", label: "Alaska (AKST)" },
  { value: "America/Los_Angeles", label: "Pacific (PST)" },
  { value: "America/Denver", label: "Mountain (MST)" },
  { value: "America/Chicago", label: "Central (CST)" },
  { value: "America/New_York", label: "Eastern (EST)" },
  { value: "America/Halifax", label: "Atlantic (AST)" },
  { value: "America/Sao_Paulo", label: "Brasilia (BRT)" },
  { value: "Atlantic/Reykjavik", label: "Iceland (GMT)" },
  { value: "Europe/London", label: "London (GMT)" },
  { value: "Europe/Paris", label: "Paris (CET)" },
  { value: "Europe/Berlin", label: "Berlin (CET)" },
  { value: "Europe/Helsinki", label: "Helsinki (EET)" },
  { value: "Europe/Moscow", label: "Moscow (MSK)" },
  { value: "Asia/Dubai", label: "Dubai (GST)" },
  { value: "Asia/Kolkata", label: "India (IST)" },
  { value: "Asia/Bangkok", label: "Bangkok (ICT)" },
  { value: "Asia/Singapore", label: "Singapore (SGT)" },
  { value: "Asia/Shanghai", label: "China (CST)" },
  { value: "Asia/Tokyo", label: "Tokyo (JST)" },
  { value: "Asia/Seoul", label: "Seoul (KST)" },
  { value: "Australia/Sydney", label: "Sydney (AEST)" },
  { value: "Australia/Melbourne", label: "Melbourne (AEST)" },
  { value: "Australia/Perth", label: "Perth (AWST)" },
  { value: "Australia/Adelaide", label: "Adelaide (ACST)" },
  { value: "Pacific/Auckland", label: "Auckland (NZST)" },
];

const VALID_TZ_VALUES = new Set(COMMON_TIMEZONES.map((tz) => tz.value));

function getClockSettings(dashboard) {
  if (!dashboard?.widget_layout) return { format: "12h", aux: [] };
  const widget = dashboard.widget_layout.find((w) => w.widget === "clock");
  const rawAux = widget?.settings?.aux ?? [];
  const aux = rawAux.map((c) => ({
    ...c,
    timezone: VALID_TZ_VALUES.has(c.timezone) ? c.timezone : "America/New_York",
  }));
  return {
    format: widget?.settings?.format ?? "12h",
    aux,
  };
}

function ClockSettings() {
  const queryClient = useQueryClient();
  const { data: dashboard } = useDashboard();
  const saved = getClockSettings(dashboard);
  const [auxClocks, setAuxClocks] = useState(saved.aux);
  const [format, setFormat] = useState(saved.format);
  const [saveStatus, setSaveStatus] = useState(null);

  function saveClockSettings(newAux, newFormat) {
    const widgetLayout = dashboard?.widget_layout ?? [];
    const clockWidget = widgetLayout.find((w) => w.widget === "clock");
    const updatedSettings = {
      ...(clockWidget?.settings ?? {}),
      aux: newAux,
      format: newFormat,
    };
    const updatedLayout = widgetLayout.map((w) =>
      w.widget === "clock" ? { ...w, settings: updatedSettings } : w
    );
    if (!clockWidget) {
      updatedLayout.push({
        widget: "clock",
        enabled: true,
        position: 0,
        settings: updatedSettings,
      });
    }
    patchDashboard({ widget_layout: updatedLayout }).then(() => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus(null), 2000);
    });
  }

  function handleAddAux() {
    if (auxClocks.length >= 3) return;
    const updated = [...auxClocks, { label: "", timezone: "America/New_York" }];
    setAuxClocks(updated);
  }

  function handleRemoveAux(index) {
    const updated = auxClocks.filter((_, i) => i !== index);
    setAuxClocks(updated);
    saveClockSettings(updated, format);
  }

  function handleAuxChange(index, field, value) {
    const updated = auxClocks.map((c, i) =>
      i === index ? { ...c, [field]: value } : c
    );
    setAuxClocks(updated);
  }

  function handleSave() {
    saveClockSettings(auxClocks, format);
  }

  function handleFormatChange(e) {
    const newFormat = e.target.value;
    setFormat(newFormat);
    saveClockSettings(auxClocks, newFormat);
  }

  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>Clock</h3>
      <label className={styles.sliderLabel}>
        <span>Time format</span>
        <select
          value={format}
          onChange={handleFormatChange}
          className={styles.textInput}
        >
          <option value="12h">12-hour</option>
          <option value="24h">24-hour</option>
        </select>
      </label>
      <div className={styles.sliderLabel}>
        <span>Auxiliary time zones ({auxClocks.length}/3)</span>
      </div>
      {auxClocks.map((clock, i) => (
        <div key={i} className={styles.auxRow}>
          <input
            type="text"
            value={clock.label}
            onChange={(e) => handleAuxChange(i, "label", e.target.value)}
            className={styles.textInput}
            placeholder="Name"
          />
          <select
            value={clock.timezone}
            onChange={(e) => handleAuxChange(i, "timezone", e.target.value)}
            className={styles.textInput}
          >
            {COMMON_TIMEZONES.map((tz) => (
              <option key={tz.value} value={tz.value}>
                {tz.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => handleRemoveAux(i)}
            className={styles.removeButton}
            title="Remove"
          >
            {"\u2715"}
          </button>
        </div>
      ))}
      <div className={styles.auxActions}>
        {auxClocks.length < 3 && (
          <button
            type="button"
            onClick={handleAddAux}
            className={styles.actionButton}
          >
            Add Time Zone
          </button>
        )}
        {auxClocks.length > 0 && (
          <button
            type="button"
            onClick={handleSave}
            className={styles.actionButton}
          >
            Save
          </button>
        )}
      </div>
      {saveStatus === "saved" && <p className={styles.success}>Saved!</p>}
    </div>
  );
}

function GoogleAccountSection() {
  const { data: auth } = useAuth();
  const googleConnected = auth?.authenticated && auth?.google_connected;

  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>Google Account</h3>
      {googleConnected ? (
        <div className={styles.accountInfo}>
          <span className={styles.email}>{auth.google_email || auth.email}</span>
          <a href="/accounts/google/login/" className={styles.linkButton}>
            Reconnect
          </a>
        </div>
      ) : (
        <a href="/accounts/google/login/" className={styles.actionButton}>
          Connect Google Account
        </a>
      )}
    </div>
  );
}

function getWordSettings(dashboard) {
  if (!dashboard?.widget_layout) return { grade_level: 1, start_date: "" };
  const widget = dashboard.widget_layout.find((w) => w.widget === "wordoftheday");
  if (!widget?.settings) return { grade_level: 1, start_date: "" };
  return {
    grade_level: widget.settings.grade_level ?? 1,
    start_date: widget.settings.start_date ?? "",
  };
}

function WordOfTheDaySettings() {
  const queryClient = useQueryClient();
  const { data: dashboard } = useDashboard();
  const saved = getWordSettings(dashboard);
  const [gradeLevel, setGradeLevel] = useState(saved.grade_level);
  const [startDate, setStartDate] = useState(saved.start_date);
  const [saveStatus, setSaveStatus] = useState(null);

  function saveSettings(updates) {
    const widgetLayout = dashboard?.widget_layout ?? [];
    const widget = widgetLayout.find((w) => w.widget === "wordoftheday");
    const currentSettings = widget?.settings ?? {};
    const updatedSettings = {
      ...currentSettings,
      grade_level: updates.grade_level ?? gradeLevel,
      start_date: updates.start_date ?? startDate,
    };
    const updatedLayout = widgetLayout.map((w) =>
      w.widget === "wordoftheday" ? { ...w, settings: updatedSettings } : w
    );
    if (!widget) {
      updatedLayout.push({
        widget: "wordoftheday",
        enabled: true,
        position: updatedLayout.length,
        panel: "left",
        settings: updatedSettings,
      });
    }
    patchDashboard({ widget_layout: updatedLayout }).then(() => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["wordoftheday"] });
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus(null), 2000);
    });
  }

  function handleGradeChange(e) {
    const val = Number(e.target.value);
    setGradeLevel(val);
    saveSettings({ grade_level: val });
  }

  function handleStartDateChange(e) {
    const val = e.target.value;
    setStartDate(val);
    saveSettings({ start_date: val });
  }

  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>Word of the Day</h3>
      <label className={styles.sliderLabel}>
        <span>Grade Level</span>
        <select
          value={gradeLevel}
          onChange={handleGradeChange}
          className={styles.textInput}
        >
          <option value={1}>Grade 1</option>
          <option value={2}>Grade 2</option>
          <option value={3}>Grade 3</option>
        </select>
      </label>
      <label className={styles.sliderLabel}>
        <span>Start date (week 1 begins here)</span>
        <input
          type="date"
          value={startDate}
          onChange={handleStartDateChange}
          className={styles.textInput}
        />
      </label>
      <p className={styles.info}>
        Leave blank to start from January of this year.
      </p>
      {saveStatus === "saved" && <p className={styles.success}>Saved!</p>}
    </div>
  );
}

function getNewsSettings(dashboard) {
  if (!dashboard?.widget_layout) {
    return { sources: [], include_keywords: [], exclude_keywords: [], rotation_interval: 30, max_headlines: 20 };
  }
  const widget = dashboard.widget_layout.find((w) => w.widget === "news");
  if (!widget?.settings) {
    return { sources: [], include_keywords: [], exclude_keywords: [], rotation_interval: 30, max_headlines: 20 };
  }
  return {
    sources: widget.settings.sources || [],
    include_keywords: widget.settings.include_keywords || [],
    exclude_keywords: widget.settings.exclude_keywords || [],
    rotation_interval: widget.settings.rotation_interval ?? 30,
    max_headlines: widget.settings.max_headlines ?? 20,
  };
}

function NewsSettings() {
  const queryClient = useQueryClient();
  const { data: dashboard } = useDashboard();
  const saved = getNewsSettings(dashboard);
  const [sources, setSources] = useState(saved.sources);
  const [includeKw, setIncludeKw] = useState(saved.include_keywords);
  const [excludeKw, setExcludeKw] = useState(saved.exclude_keywords);
  const [rotationInterval, setRotationInterval] = useState(saved.rotation_interval);
  const [maxHeadlines, setMaxHeadlines] = useState(saved.max_headlines);
  const [newFeedName, setNewFeedName] = useState("");
  const [newFeedUrl, setNewFeedUrl] = useState("");
  const [newGoogleKeyword, setNewGoogleKeyword] = useState("");
  const [newIncludeKw, setNewIncludeKw] = useState("");
  const [newExcludeKw, setNewExcludeKw] = useState("");
  const [saveStatus, setSaveStatus] = useState(null);

  function saveNewsSettings(updates) {
    const widgetLayout = dashboard?.widget_layout ?? [];
    const newsWidget = widgetLayout.find((w) => w.widget === "news");
    const currentSettings = newsWidget?.settings ?? {};
    const updatedSettings = {
      ...currentSettings,
      sources: updates.sources ?? sources,
      include_keywords: updates.include_keywords ?? includeKw,
      exclude_keywords: updates.exclude_keywords ?? excludeKw,
      rotation_interval: updates.rotation_interval ?? rotationInterval,
      max_headlines: updates.max_headlines ?? maxHeadlines,
    };
    const updatedLayout = widgetLayout.map((w) =>
      w.widget === "news" ? { ...w, settings: updatedSettings } : w
    );
    if (!newsWidget) {
      updatedLayout.push({
        widget: "news",
        enabled: true,
        position: updatedLayout.length,
        panel: "right",
        settings: updatedSettings,
      });
    }
    patchDashboard({ widget_layout: updatedLayout }).then(() => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["news"] });
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus(null), 2000);
    });
  }

  function handleAddFeed() {
    const url = newFeedUrl.trim();
    const name = newFeedName.trim();
    if (!url) return;
    const updated = [...sources, { name: name || url, url }];
    setSources(updated);
    setNewFeedName("");
    setNewFeedUrl("");
    saveNewsSettings({ sources: updated });
  }

  function handleAddGoogleNews() {
    const keyword = newGoogleKeyword.trim();
    if (!keyword) return;
    const url = `https://news.google.com/rss/search?q=${encodeURIComponent(keyword)}&hl=en-US&gl=US&ceid=US:en`;
    const updated = [
      ...sources,
      { name: `Google News: ${keyword}`, url, type: "google_news", keyword },
    ];
    setSources(updated);
    setNewGoogleKeyword("");
    saveNewsSettings({ sources: updated });
  }

  function handleRemoveSource(index) {
    const updated = sources.filter((_, i) => i !== index);
    setSources(updated);
    saveNewsSettings({ sources: updated });
  }

  function handleAddIncludeKw() {
    const kw = newIncludeKw.trim().toLowerCase();
    if (!kw || includeKw.includes(kw)) return;
    const updated = [...includeKw, kw];
    setIncludeKw(updated);
    setNewIncludeKw("");
    saveNewsSettings({ include_keywords: updated });
  }

  function handleRemoveIncludeKw(index) {
    const updated = includeKw.filter((_, i) => i !== index);
    setIncludeKw(updated);
    saveNewsSettings({ include_keywords: updated });
  }

  function handleAddExcludeKw() {
    const kw = newExcludeKw.trim().toLowerCase();
    if (!kw || excludeKw.includes(kw)) return;
    const updated = [...excludeKw, kw];
    setExcludeKw(updated);
    setNewExcludeKw("");
    saveNewsSettings({ exclude_keywords: updated });
  }

  function handleRemoveExcludeKw(index) {
    const updated = excludeKw.filter((_, i) => i !== index);
    setExcludeKw(updated);
    saveNewsSettings({ exclude_keywords: updated });
  }

  function handleRotationChange(e) {
    const val = Number(e.target.value);
    setRotationInterval(val);
    saveNewsSettings({ rotation_interval: val });
  }

  function handleMaxHeadlinesChange(e) {
    const val = Number(e.target.value);
    setMaxHeadlines(val);
    saveNewsSettings({ max_headlines: val });
  }

  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>News Feeds</h3>

      {sources.length > 0 && (
        <div className={styles.newsList}>
          {sources.map((source, i) => (
            <div key={i} className={styles.newsSourceRow}>
              <div className={styles.newsSourceInfo}>
                <span className={styles.newsSourceName}>{source.name}</span>
                {source.type === "google_news" && (
                  <span className={styles.newsSourceBadge}>Google News</span>
                )}
              </div>
              <button
                type="button"
                onClick={() => handleRemoveSource(i)}
                className={styles.removeButton}
                title="Remove"
              >
                {"\u2715"}
              </button>
            </div>
          ))}
        </div>
      )}

      <div className={styles.newsAddSection}>
        <span className={styles.newsAddLabel}>Add RSS feed</span>
        <input
          type="text"
          value={newFeedName}
          onChange={(e) => setNewFeedName(e.target.value)}
          className={styles.textInput}
          placeholder="Feed name (optional)"
        />
        <div className={styles.newsAddRow}>
          <input
            type="url"
            value={newFeedUrl}
            onChange={(e) => setNewFeedUrl(e.target.value)}
            className={styles.textInput}
            placeholder="https://example.com/rss.xml"
            onKeyDown={(e) => e.key === "Enter" && handleAddFeed()}
          />
          <button
            type="button"
            onClick={handleAddFeed}
            className={styles.actionButton}
            disabled={!newFeedUrl.trim()}
          >
            Add
          </button>
        </div>
      </div>

      <div className={styles.newsAddSection}>
        <span className={styles.newsAddLabel}>Add Google News search</span>
        <div className={styles.newsAddRow}>
          <input
            type="text"
            value={newGoogleKeyword}
            onChange={(e) => setNewGoogleKeyword(e.target.value)}
            className={styles.textInput}
            placeholder='Keyword (e.g. "artificial intelligence")'
            onKeyDown={(e) => e.key === "Enter" && handleAddGoogleNews()}
          />
          <button
            type="button"
            onClick={handleAddGoogleNews}
            className={styles.actionButton}
            disabled={!newGoogleKeyword.trim()}
          >
            Add
          </button>
        </div>
      </div>

      <div className={styles.newsAddSection}>
        <span className={styles.newsAddLabel}>Include keywords (show only matching)</span>
        <div className={styles.newsKeywordList}>
          {includeKw.map((kw, i) => (
            <span key={i} className={styles.newsKeywordTag}>
              {kw}
              <button
                type="button"
                onClick={() => handleRemoveIncludeKw(i)}
                className={styles.newsKeywordRemove}
              >
                {"\u2715"}
              </button>
            </span>
          ))}
        </div>
        <div className={styles.newsAddRow}>
          <input
            type="text"
            value={newIncludeKw}
            onChange={(e) => setNewIncludeKw(e.target.value)}
            className={styles.textInput}
            placeholder="Add keyword..."
            onKeyDown={(e) => e.key === "Enter" && handleAddIncludeKw()}
          />
          <button
            type="button"
            onClick={handleAddIncludeKw}
            className={styles.actionButton}
            disabled={!newIncludeKw.trim()}
          >
            Add
          </button>
        </div>
      </div>

      <div className={styles.newsAddSection}>
        <span className={styles.newsAddLabel}>Exclude keywords (hide matching)</span>
        <div className={styles.newsKeywordList}>
          {excludeKw.map((kw, i) => (
            <span key={i} className={styles.newsKeywordTagExclude}>
              {kw}
              <button
                type="button"
                onClick={() => handleRemoveExcludeKw(i)}
                className={styles.newsKeywordRemove}
              >
                {"\u2715"}
              </button>
            </span>
          ))}
        </div>
        <div className={styles.newsAddRow}>
          <input
            type="text"
            value={newExcludeKw}
            onChange={(e) => setNewExcludeKw(e.target.value)}
            className={styles.textInput}
            placeholder="Add keyword..."
            onKeyDown={(e) => e.key === "Enter" && handleAddExcludeKw()}
          />
          <button
            type="button"
            onClick={handleAddExcludeKw}
            className={styles.actionButton}
            disabled={!newExcludeKw.trim()}
          >
            Add
          </button>
        </div>
      </div>

      <label className={styles.sliderLabel}>
        <span>Rotate every {rotationInterval}s</span>
        <input
          type="range"
          min="5"
          max="120"
          step="5"
          value={rotationInterval}
          onChange={handleRotationChange}
          className={styles.slider}
        />
      </label>

      <label className={styles.sliderLabel}>
        <span>Max headlines: {maxHeadlines}</span>
        <input
          type="range"
          min="5"
          max="50"
          step="5"
          value={maxHeadlines}
          onChange={handleMaxHeadlinesChange}
          className={styles.slider}
        />
      </label>

      {saveStatus === "saved" && <p className={styles.success}>Saved!</p>}
    </div>
  );
}

function KioskModeSection({ kioskMode, onToggle }) {
  return (
    <div className={styles.section}>
      <h3 className={styles.sectionTitle}>Kiosk Mode</h3>
      <p className={styles.info}>
        {kioskMode
          ? "External links are disabled. Tapping widgets won\u2019t navigate away."
          : "Tapping stocks, news, or calendar opens links in new tabs."}
      </p>
      <button type="button" onClick={onToggle} className={styles.actionButton}>
        {kioskMode ? "Disable Kiosk Mode" : "Enable Kiosk Mode"}
      </button>
    </div>
  );
}

export default function SettingsPanel({ onClose, photoFrameMode, onTogglePhotoFrame, kioskMode, onToggleKiosk }) {
  const { data: auth } = useAuth();
  const { data: dashboard } = useDashboard();
  const googleConnected = auth?.authenticated && auth?.google_connected;
  const hasPhotos = getSavedPhotoCount(dashboard) > 0;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.panel} onClick={(e) => e.stopPropagation()}>
        <div className={styles.panelHeader}>
          <h2 className={styles.panelTitle}>Settings</h2>
          <button
            type="button"
            onClick={onClose}
            className={styles.closeButton}
            aria-label="Close settings"
          >
            {"\u2715"}
          </button>
        </div>
        <LayoutEditor />
        <KioskModeSection kioskMode={kioskMode} onToggle={onToggleKiosk} />
        <ClockSettings />
        <WordOfTheDaySettings />
        <NewsSettings />
        <PhotoFrameSection
          photoFrameMode={photoFrameMode}
          onToggle={onTogglePhotoFrame}
          hasPhotos={hasPhotos}
        />
        <DexcomSettings />
        {googleConnected && <PhotosPicker />}
        <GoogleAccountSection />
      </div>
    </div>
  );
}

function getSavedPickerSessionId(dashboard) {
  if (!dashboard?.widget_layout) return null;
  const photoWidget = dashboard.widget_layout.find((w) => w.widget === "photos");
  return photoWidget?.settings?.picker_session_id ?? null;
}

function getSavedPhotoCount(dashboard) {
  if (!dashboard?.widget_layout) return 0;
  const photoWidget = dashboard.widget_layout.find((w) => w.widget === "photos");
  return photoWidget?.settings?.cached_media?.length ?? 0;
}
