import { createContext, useContext } from "react"

interface NotebookContextType {
  showNotebook: boolean
  setShowNotebook: (show: boolean) => void
}

const NotebookContext = createContext<NotebookContextType | undefined>(undefined)

export function useNotebook() {
  const context = useContext(NotebookContext)
  if (!context) {
    throw new Error("useNotebook must be used within NotebookProvider")
  }
  return context
}

export default NotebookContext
