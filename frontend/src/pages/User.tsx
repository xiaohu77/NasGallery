import { useNavigate } from 'react-router-dom'
import { useUser } from '../contexts/UserContext'

const User = (): JSX.Element => {
  const navigate = useNavigate()
  const { user, logout } = useUser()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-6 text-white">
            <h1 className="text-2xl font-bold">用户中心</h1>
            <p className="text-blue-100 mt-1">管理您的账户信息</p>
          </div>

          {/* User Info */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-blue-600 dark:text-blue-300">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {user?.username || '未登录'}
                </h2>
                <p className="text-gray-600 dark:text-gray-400">
                  {user?.email || '未设置邮箱'}
                </p>
              </div>
            </div>
          </div>

          {/* Account Details */}
          <div className="p-6 space-y-4">
            <div className="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <span className="text-gray-700 dark:text-gray-300">用户ID</span>
              <span className="text-gray-900 dark:text-white font-medium">
                {user?.id || '-'}
              </span>
            </div>
            <div className="flex justify-between items-center py-3 border-b border-gray-100 dark:border-gray-700">
              <span className="text-gray-700 dark:text-gray-300">注册时间</span>
              <span className="text-gray-900 dark:text-white font-medium">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString('zh-CN')
                  : '-'}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="p-6 bg-gray-50 dark:bg-gray-900/50">
            <button
              onClick={handleLogout}
              className="w-full py-3 px-4 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
            >
              退出登录
            </button>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            快捷操作
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => navigate('/')}
              className="py-3 px-4 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors"
            >
              返回首页
            </button>
            <button
              onClick={() => navigate('/')}
              className="py-3 px-4 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors"
            >
              浏览相册
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default User
