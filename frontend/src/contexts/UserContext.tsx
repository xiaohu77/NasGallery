import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { ReactNode } from 'react'
import { User, UserContextType } from '../types/user'

const API_BASE = import.meta.env.VITE_API_BASE || 'https://back.xiaohu777.cn'

const UserContext = createContext<UserContextType | null>(null)

export const UserProvider = ({ children }: { children: ReactNode }): JSX.Element => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // 从 localStorage 恢复登录状态
  useEffect(() => {
    const savedToken = localStorage.getItem('auth_token')
    const savedUser = localStorage.getItem('auth_user')

    if (savedToken && savedUser) {
      try {
        const parsedUser: User = JSON.parse(savedUser)
        setToken(savedToken)
        setUser(parsedUser)
      } catch (error) {
        console.error('Failed to parse saved user data:', error)
        localStorage.removeItem('auth_token')
        localStorage.removeItem('auth_user')
      }
    }
    setIsLoading(false)
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      })

      if (!response.ok) {
        throw new Error('登录失败')
      }

      const data = await response.json()
      const { access_token, user: userData } = data

      // 保存到状态
      setToken(access_token)
      setUser(userData)

      // 保存到 localStorage
      localStorage.setItem('auth_token', access_token)
      localStorage.setItem('auth_user', JSON.stringify(userData))
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }, [])

  const register = useCallback(async (username: string, email: string, password: string) => {
    try {
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email, password })
      })

      if (!response.ok) {
        throw new Error('注册失败')
      }

      const data = await response.json()
      const { access_token, user: userData } = data

      // 保存到状态
      setToken(access_token)
      setUser(userData)

      // 保存到 localStorage
      localStorage.setItem('auth_token', access_token)
      localStorage.setItem('auth_user', JSON.stringify(userData))
    } catch (error) {
      console.error('Register error:', error)
      throw error
    }
  }, [])

  const logout = useCallback(() => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  }, [])

  const isAuthenticated = !!token && !!user

  const value: UserContextType = {
    user,
    token,
    isLoading,
    login,
    register,
    logout,
    isAuthenticated
  }

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>
}

export const useUser = (): UserContextType => {
  const context = useContext(UserContext)
  if (!context) {
    throw new Error('useUser must be used within a UserProvider')
  }
  return context
}
