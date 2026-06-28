export function useToast() {
  return {
    success: (message: string) => {
      console.log("✓", message)
    },
    error: (message: string) => {
      console.error("✗", message)
    },
  }
}
