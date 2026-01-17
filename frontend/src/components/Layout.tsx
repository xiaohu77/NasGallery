import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'

const Layout = (): JSX.Element => {
  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <Header />
      <div className="flex pt-12 lg:pt-0">
        <Sidebar />
        <main className="flex-1 lg:pl-64 hide-scrollbar">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout