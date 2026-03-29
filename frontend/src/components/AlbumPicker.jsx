import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchGooglePhotosAlbums, patchDashboard } from "../api/auth";
import { useDashboard } from "../hooks/useDashboard";
import WidgetCard from "./WidgetCard";
import styles from "./AlbumPicker.module.css";

export default function AlbumPicker() {
  const queryClient = useQueryClient();
  const { data: dashboard } = useDashboard();
  const { data: albums, isLoading, isError } = useQuery({
    queryKey: ["googlePhotosAlbums"],
    queryFn: fetchGooglePhotosAlbums,
  });

  const selectedAlbumId = getSavedAlbumId(dashboard);

  function handleSelect(albumId) {
    const next = selectedAlbumId === albumId ? null : albumId;
    const widgetLayout = dashboard?.widget_layout ?? [];
    const photoWidget = widgetLayout.find((w) => w.widget === "photos");
    const updatedSettings = { ...(photoWidget?.settings ?? {}), google_album_id: next };
    const updatedLayout = widgetLayout.map((w) =>
      w.widget === "photos" ? { ...w, settings: updatedSettings } : w
    );
    if (!photoWidget) {
      updatedLayout.push({
        widget: "photos",
        enabled: true,
        position: updatedLayout.length,
        settings: { google_album_id: next },
      });
    }
    patchDashboard({ widget_layout: updatedLayout }).then(() =>
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
    );
  }

  if (isLoading) {
    return (
      <WidgetCard title="Photo Albums">
        <div className={styles.loading}>Loading albums...</div>
      </WidgetCard>
    );
  }

  if (isError || !albums) {
    return null;
  }

  if (albums.length === 0) {
    return (
      <WidgetCard title="Photo Albums">
        <div className={styles.empty}>No albums found</div>
      </WidgetCard>
    );
  }

  return (
    <WidgetCard title="Photo Albums">
      <div className={styles.grid}>
        {albums.map((album) => (
          <button
            key={album.id}
            className={`${styles.albumCard} ${selectedAlbumId === album.id ? styles.selected : ""}`}
            onClick={() => handleSelect(album.id)}
            type="button"
          >
            {album.cover_photo_url ? (
              <img
                src={album.cover_photo_url}
                alt={album.title}
                className={styles.cover}
              />
            ) : (
              <div className={styles.placeholder} />
            )}
            <span className={styles.albumTitle}>{album.title}</span>
            {album.media_items_count != null && (
              <span className={styles.count}>{album.media_items_count} items</span>
            )}
          </button>
        ))}
      </div>
    </WidgetCard>
  );
}

function getSavedAlbumId(dashboard) {
  if (!dashboard?.widget_layout) return null;
  const photoWidget = dashboard.widget_layout.find((w) => w.widget === "photos");
  return photoWidget?.settings?.google_album_id ?? null;
}
