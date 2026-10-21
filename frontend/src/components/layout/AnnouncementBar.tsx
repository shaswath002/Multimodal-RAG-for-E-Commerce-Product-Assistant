/** Announcement bar – gold strip with the single message */
const MESSAGE = 'Compare prices across stores before you buy.'

export default function AnnouncementBar() {
  return (
    <div
      role="banner"
      aria-label="Site announcement"
      style={{
        backgroundColor: 'var(--champagne)',
        color: '#000000',
        height: '40px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '0.75rem',
        letterSpacing: '0.06em',
        fontWeight: 600,
      }}
    >
      <div className="container" style={{ textAlign: 'center' }}>
        {MESSAGE}
      </div>
    </div>
  )
}
