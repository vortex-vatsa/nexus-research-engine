import { auth } from "@/auth"

export default auth((req) => {
  const isLoggedIn = !!req.auth
  const isLoginPage = req.nextUrl.pathname.startsWith("/login")
  const isAuthRoute = req.nextUrl.pathname.startsWith("/api/auth")

  if (!isLoggedIn && !isLoginPage && !isAuthRoute) {
    return Response.redirect(new URL("/login", req.nextUrl))
  }
})

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
}
