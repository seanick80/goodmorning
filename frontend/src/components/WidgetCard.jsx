import styles from "./WidgetCard.module.css";

export default function WidgetCard({ title, titleExtra, children, className }) {
  return (
    <div className={`${styles.card} ${className || ""}`}>
      {title && (
        <h2 className={styles.title}>
          {title}
          {titleExtra}
        </h2>
      )}
      <div className={styles.content}>{children}</div>
    </div>
  );
}
