import { useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  DndContext,
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
  arrayMove,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useDroppable } from "@dnd-kit/core";
import { useDashboard } from "../hooks/useDashboard";
import { patchDashboard } from "../api/auth";
import styles from "./LayoutEditor.module.css";

const WIDGET_NAMES = {
  clock: "Clock",
  weather: "Weather",
  stocks: "Stocks",
  calendar: "Calendar",
  news: "News",
  glucose: "Glucose",
  photos: "Photos",
};

const DEFAULT_PANELS = {
  left: ["clock", "weather"],
  right: ["glucose", "stocks", "calendar", "news"],
};

function buildPanelsFromLayout(widgetLayout) {
  if (!widgetLayout || widgetLayout.length === 0) {
    return { ...DEFAULT_PANELS };
  }

  const left = [];
  const right = [];
  const defaultPanel = {
    clock: "left",
    weather: "left",
    glucose: "right",
    stocks: "right",
    calendar: "right",
    news: "right",
    photos: "right",
  };

  const sorted = [...widgetLayout].sort(
    (a, b) => (a.position ?? 0) - (b.position ?? 0)
  );

  for (const w of sorted) {
    if (!WIDGET_NAMES[w.widget]) continue;
    const panel = w.panel || defaultPanel[w.widget] || "right";
    if (panel === "left") left.push(w.widget);
    else right.push(w.widget);
  }

  // Add any widgets from WIDGET_NAMES that aren't in the layout
  for (const key of Object.keys(WIDGET_NAMES)) {
    if (!left.includes(key) && !right.includes(key)) {
      const panel = defaultPanel[key] || "right";
      if (panel === "left") left.push(key);
      else right.push(key);
    }
  }

  return { left, right };
}

function buildEnabledFromLayout(widgetLayout) {
  const enabled = {};
  for (const key of Object.keys(WIDGET_NAMES)) {
    enabled[key] = true;
  }
  if (widgetLayout) {
    for (const w of widgetLayout) {
      if (WIDGET_NAMES[w.widget]) {
        enabled[w.widget] = w.enabled !== false;
      }
    }
  }
  return enabled;
}

function DroppablePanel({ id, children, title }) {
  const { setNodeRef } = useDroppable({ id });
  return (
    <div ref={setNodeRef} className={styles.panelColumn}>
      <h4 className={styles.panelTitle}>{title}</h4>
      <div className={styles.panelItems}>{children}</div>
    </div>
  );
}

function SortableWidgetCard({ id, enabled, onToggle }) {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`${styles.widgetCard} ${!enabled ? styles.disabled : ""}`}
    >
      <span {...attributes} {...listeners} className={styles.dragHandle}>
        {"\u2630"}
      </span>
      <span className={styles.widgetName}>{WIDGET_NAMES[id]}</span>
      <label className={styles.toggle}>
        <input
          type="checkbox"
          checked={enabled}
          onChange={() => onToggle(id)}
        />
        <span className={styles.toggleSlider} />
      </label>
    </div>
  );
}

function findContainer(id, panels) {
  if (id in panels) return id;
  return Object.keys(panels).find((key) => panels[key].includes(id));
}

export default function LayoutEditor() {
  const queryClient = useQueryClient();
  const { data: dashboard } = useDashboard();
  const [panels, setPanels] = useState(() =>
    buildPanelsFromLayout(dashboard?.widget_layout)
  );
  const [enabled, setEnabled] = useState(() =>
    buildEnabledFromLayout(dashboard?.widget_layout)
  );
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  const handleToggle = useCallback((id) => {
    setEnabled((prev) => ({ ...prev, [id]: !prev[id] }));
  }, []);

  function handleDragOver(event) {
    const { active, over } = event;
    if (!over) return;

    const activeContainer = findContainer(active.id, panels);
    const overContainer = findContainer(over.id, panels);

    if (!activeContainer || !overContainer || activeContainer === overContainer)
      return;

    setPanels((prev) => {
      const activeItems = [...prev[activeContainer]];
      const overItems = [...prev[overContainer]];
      const activeIndex = activeItems.indexOf(active.id);
      const overIndex = overItems.indexOf(over.id);

      activeItems.splice(activeIndex, 1);
      const insertAt = overIndex >= 0 ? overIndex : overItems.length;
      overItems.splice(insertAt, 0, active.id);

      return {
        ...prev,
        [activeContainer]: activeItems,
        [overContainer]: overItems,
      };
    });
  }

  function handleDragEnd(event) {
    const { active, over } = event;
    if (!over) return;

    const activeContainer = findContainer(active.id, panels);
    const overContainer = findContainer(over.id, panels);

    if (!activeContainer || !overContainer) return;

    if (activeContainer === overContainer) {
      const items = panels[activeContainer];
      const oldIndex = items.indexOf(active.id);
      const newIndex = items.indexOf(over.id);
      if (oldIndex !== newIndex) {
        setPanels((prev) => ({
          ...prev,
          [activeContainer]: arrayMove(
            prev[activeContainer],
            oldIndex,
            newIndex
          ),
        }));
      }
    }
  }

  async function handleSave() {
    setSaving(true);
    setSaveStatus(null);
    try {
      const existingLayout = dashboard?.widget_layout ?? [];
      const newLayout = [];

      for (const panelName of ["left", "right"]) {
        const items = panels[panelName];
        items.forEach((widgetId, index) => {
          const existing = existingLayout.find((w) => w.widget === widgetId);
          newLayout.push({
            widget: widgetId,
            enabled: enabled[widgetId] ?? true,
            panel: panelName,
            position: index,
            settings: existing?.settings ?? {},
          });
        });
      }

      await patchDashboard({ widget_layout: newLayout });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus(null), 2000);
    } catch {
      setSaveStatus("error");
    } finally {
      setSaving(false);
    }
  }

  function handleReset() {
    setPanels({ ...DEFAULT_PANELS });
    const resetEnabled = {};
    for (const key of Object.keys(WIDGET_NAMES)) {
      resetEnabled[key] = true;
    }
    setEnabled(resetEnabled);
  }

  return (
    <div className={styles.editor}>
      <h3 className={styles.sectionTitle}>Widget Layout</h3>
      <DndContext
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div className={styles.columns}>
          <DroppablePanel id="left" title="Left Panel">
            <SortableContext
              items={panels.left}
              strategy={verticalListSortingStrategy}
            >
              {panels.left.map((id) => (
                <SortableWidgetCard
                  key={id}
                  id={id}
                  enabled={enabled[id]}
                  onToggle={handleToggle}
                />
              ))}
            </SortableContext>
          </DroppablePanel>
          <DroppablePanel id="right" title="Right Panel">
            <SortableContext
              items={panels.right}
              strategy={verticalListSortingStrategy}
            >
              {panels.right.map((id) => (
                <SortableWidgetCard
                  key={id}
                  id={id}
                  enabled={enabled[id]}
                  onToggle={handleToggle}
                />
              ))}
            </SortableContext>
          </DroppablePanel>
        </div>
      </DndContext>
      <div className={styles.actions}>
        <button
          type="button"
          onClick={handleSave}
          className={styles.actionButton}
          disabled={saving}
        >
          {saving ? "Saving..." : "Save Layout"}
        </button>
        <button
          type="button"
          onClick={handleReset}
          className={styles.actionButton}
        >
          Reset to Default
        </button>
      </div>
      {saveStatus === "saved" && (
        <p className={styles.success}>Layout saved!</p>
      )}
      {saveStatus === "error" && (
        <p className={styles.errorText}>Failed to save. Please try again.</p>
      )}
    </div>
  );
}
