/**
 * 用户类型定义
 */

export interface User {
  id: number
  username: string
  email: string
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface UserContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}
