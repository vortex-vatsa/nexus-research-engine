import "next-auth"

declare module "next-auth" {
  interface Session {
    nexusToken?: string
    accessToken?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    nexusToken?: string
    accessToken?: string
  }
}
