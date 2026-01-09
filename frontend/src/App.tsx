import { Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { OfflineProvider } from './contexts/OfflineContext'
import Layout from './components/Layout'
import Home from './pages/Home'
import AlbumDetail from './pages/AlbumDetail'

function App(): JSX.Element {
  return (
    <ThemeProvider>
      <OfflineProvider>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="/org/:id" element={<Home />} />
            <Route path="/model/:id" element={<Home />} />
            <Route path="/tag/:id" element={<Home />} />
            <Route path="/album/:id" element={<AlbumDetail />} />
          </Route>
        </Routes>
      </OfflineProvider>
    </ThemeProvider>
  )
}

export default App