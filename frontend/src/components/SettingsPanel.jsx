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

export default function SettingsPanel({ onClose }) {
  const { data: auth } = useAuth();
  const googleConnected = auth?.authenticated && auth?.google_connected;

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
