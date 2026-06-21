import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
  })
}

export function getDomain(url: string): string {
  try {
    return new URL(url).hostname.replace("www.", "")
  } catch {
    return url
  }
}
