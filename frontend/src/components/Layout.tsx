import { Outlet, useLocation } from 'react-router-dom'
import Header from './Header'

const Layout = (): JSX.Element => {
  const location = useLocation()
  const hideHeader = location.pathname.startsWith('/album/') || location.pathname.startsWith('/settings')

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      {!hideHeader && <Header />}
      <main 
        key={location.pathname} 
        className={`page-transition ${hideHeader ? 'pt-0' : 'pt-28'}`}
      >
        <Outlet />
      </main>
    </div>
  )
}

export default Layout
