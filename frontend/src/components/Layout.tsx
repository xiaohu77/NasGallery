import { Outlet, useLocation } from 'react-router-dom'
import Header from './Header'

const Layout = (): JSX.Element => {
  const location = useLocation()
  const showHeader = !location.pathname.startsWith('/album/')

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      {showHeader && <Header />}
      <main 
        key={location.pathname} 
        className={`page-transition ${showHeader ? 'pt-28' : 'pt-0'}`}
      >
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
