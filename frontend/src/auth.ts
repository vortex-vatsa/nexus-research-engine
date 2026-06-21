import NextAuth from "next-auth"
import Google from "next-auth/providers/google"

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [Google],
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account) {
        token.email = profile?.email
        token.accessToken = account.access_token
      }
      return token
    },
    async session({ session, token }) {
      session.user.email = token.email as string
      session.accessToken = token.accessToken as string
      return session
    },
  },
  pages: { signIn: "/login" },
})
