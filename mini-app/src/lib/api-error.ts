import type { ApiError } from "../api";

export function isApiError(value: unknown): value is ApiError {
  return typeof value === "object" && value !== null && "status" in value && "detail" in value;
}

export function errorMessage(err: unknown): string {
  if (isApiError(err)) return err.detail;
  if (err instanceof Error) return err.message;
  return String(err);
}
