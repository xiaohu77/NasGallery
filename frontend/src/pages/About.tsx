const About = (): JSX.Element => {
  const appInfo = {
    name: 'NasGallery',
    version: '1.0.0',
    author: '程序员零一',
    github: 'https://github.com/xiaohu77/NasGallery',
    wechat: 'wwg867376690',
    publicAccount: '程序员零一',
    description: '一个现代化的 Web 应用，用于管理和查看 CBZ 图片档案'
  }

  return (
    <div className="min-h-screen bg-gray-50/50 dark:bg-gray-950">
      <div className="max-w-xl mx-auto px-4 pt-6 pb-8">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">关于</h1>
        <p className="text-sm text-gray-500 mb-8">应用信息与联系方式</p>

        {/* 应用信息卡片 */}
        <div className="backdrop-blur-xl bg-white/60 dark:bg-gray-900/60 rounded-3xl p-6 mb-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-2xl overflow-hidden">
              <img 
                src="/icon-512.png" 
                alt="NasGallery" 
                className="w-full h-full object-cover"
              />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">{appInfo.name}</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">{appInfo.description}</p>
            </div>
          </div>

          <div className="space-y-4">
            <InfoRow label="版本" value={appInfo.version} />
            <InfoRow label="作者" value={appInfo.author} />
            <InfoRow label="公众号" value={appInfo.publicAccount} />
            <InfoRow 
              label="GitHub" 
              value={
                <a 
                  href={appInfo.github} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  {appInfo.github.replace('https://', '')}
                </a>
              } 
            />
            <InfoRow label="微信" value={appInfo.wechat} />
          </div>
        </div>

        {/* 开源协议 */}
        <div className="backdrop-blur-xl bg-white/60 dark:bg-gray-900/60 rounded-3xl p-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-green-500/10 flex items-center justify-center">
              <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-900 dark:text-white">MIT License</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">开源协议</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const InfoRow = ({ label, value }: { label: string, value: React.ReactNode }) => (
  <div className="flex items-center justify-between py-2 border-b border-gray-200/50 dark:border-gray-700/50 last:border-0">
    <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
    <span className="text-sm font-medium text-gray-900 dark:text-white">{value}</span>
  </div>
)

export default About
