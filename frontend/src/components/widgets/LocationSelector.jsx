import { useState, useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { searchLocations, updateWeatherLocation } from "../../api/geocode";
import styles from "./LocationSelector.module.css";

export default function LocationSelector() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);
  const queryClient = useQueryClient();
  const debounceRef = useRef(null);

  const doSearch = useCallback((q) => {
    if (q.length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    searchLocations(q)
      .then((data) => setResults(data))
      .catch(() => setResults([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(query), 300);
    return () => clearTimeout(debounceRef.current);
  }, [query, isOpen, doSearch]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  function handleSelect(location) {
    setIsOpen(false);
    setQuery("");
    setResults([]);
    updateWeatherLocation(
      location.latitude,
      location.longitude,
      location.display_name
    ).then(() => {
      queryClient.invalidateQueries({ queryKey: ["weather"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    });
  }

  function handleClose() {
    setIsOpen(false);
    setQuery("");
    setResults([]);
  }

  if (!isOpen) {
    return (
      <button
        className={styles.editButton}
        onClick={() => setIsOpen(true)}
        title="Change location"
      >
        &#9998;
      </button>
    );
  }

  return (
    <>
      <div className={styles.overlay} onClick={handleClose} />
      <span className={styles.wrapper}>
        <input
          ref={inputRef}
          className={styles.input}
          type="text"
          placeholder="Search city..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Escape" && handleClose()}
        />
        {(results.length > 0 || (query.length >= 2 && !loading)) && (
          <div className={styles.dropdown}>
            <ul className={styles.results}>
              {results.map((loc, i) => (
                <li
                  key={i}
                  className={styles.resultItem}
                  onClick={() => handleSelect(loc)}
                >
                  {loc.display_name}
                </li>
              ))}
              {results.length === 0 && query.length >= 2 && !loading && (
                <li className={styles.noResults}>No results found</li>
              )}
            </ul>
          </div>
        )}
      </span>
    </>
  );
}
