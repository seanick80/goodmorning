import { useAuth } from "../hooks/useAuth";
import styles from "./AuthStatus.module.css";

export default function AuthStatus() {
  const { data: auth, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!auth?.authenticated) {
    return (
      <div className={styles.container}>
        <a href="/accounts/google/login/" className={styles.signInButton}>
          Sign in with Google
        </a>
      </div>
    );
  }

  const displayName = auth.google_name || auth.username;
  const avatarUrl = auth.google_picture;

  return (
    <div className={styles.container}>
      <div className={styles.userInfo}>
        {avatarUrl && (
          <img
            src={avatarUrl}
            alt={displayName}
            className={styles.avatar}
            referrerPolicy="no-referrer"
          />
        )}
        <span className={styles.name}>{displayName}</span>
      </div>
      <form method="POST" action="/accounts/logout/" className={styles.logoutForm}>
        <button type="submit" className={styles.signOutButton}>
          Sign out
        </button>
      </form>
    </div>
  );
}
