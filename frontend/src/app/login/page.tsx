import { signIn } from "@/auth"

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-base flex items-center justify-center p-4">
      <div className="text-center space-y-6 max-w-sm">
        <h1 className="text-4xl font-bold text-accent">NEXUS</h1>
        <p className="text-muted text-lg">Autonomous Research Engine</p>
        <form
          action={async () => {
            "use server"
            await signIn("google", { redirectTo: "/" })
          }}
        >
          <button
            type="submit"
            className="w-full px-6 py-3 bg-accent text-white rounded-lg font-semibold hover:bg-accent/90 transition-colors"
          >
            Sign in with Google
          </button>
        </form>
        <p className="text-muted text-sm mt-8">
          Nexus is a private research engine. Access is restricted to authorized users.
        </p>
      </div>
    </main>
  )
}
