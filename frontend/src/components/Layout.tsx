import { Outlet } from 'react-router-dom'
import Header from './Header'

const Layout = (): JSX.Element => {
  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <Header />
      <main className="pt-28">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout