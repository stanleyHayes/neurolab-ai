"use client";
import { useEffect, useState } from "react";
import { authenticatedFetch } from "../auth-client";

export function useInferenceAvailability() {
  const [availability, setAvailability] = useState({
    enabled: false,
    checking: true,
    reason: "Checking inference availability…",
  });
  useEffect(() => {
    const controller = new AbortController();
    void authenticatedFetch("/api/research-capabilities", {
      signal: controller.signal,
      cache: "no-store",
    })
      .then(async (response) => {
        if (!response.ok)
          throw new Error(
            "Availability could not be checked. Deterministic analysis remains available.",
          );
        const value = await response.json();
        if (!controller.signal.aborted)
          setAvailability({
            enabled: value.model_inference_enabled === true,
            checking: false,
            reason:
              typeof value.inference_message === "string"
                ? value.inference_message
                : "Live model access is unavailable.",
          });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setAvailability({
            enabled: false,
            checking: false,
            reason:
              error instanceof Error
                ? error.message
                : "Live model access is unavailable.",
          });
      });
    return () => controller.abort();
  }, []);
  return availability;
}
