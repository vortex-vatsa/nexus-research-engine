import NextAuth from "next-auth"
import Google from "next-auth/providers/google"

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_ID!,
      clientSecret: process.env.AUTH_GOOGLE_SECRET!,
      authorization: {
        params: { scope: "openid email profile" },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account?.id_token) {
        try {
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/auth/token`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ google_id_token: account.id_token }),
            }
          )
          if (res.ok) {
            const data = await res.json()
            token.nexusToken = data.access_token
          }
        } catch (e) {
          console.error("Token exchange failed:", e)
        }
      }
      return token
    },
    async session({ session, token }) {
      session.nexusToken = token.nexusToken as string
      return session
    },
  },
  pages: { signIn: "/login" },
})
