const loadingSpinner = document.getElementById('loading-spinner')

export default function setLoading (loading: boolean) {
  return
  if (loading) {
    loadingSpinner.style.display = 'block'
  } else {
    setTimeout(() => {
      loadingSpinner.style.display = 'none'
    }, 50)
  }
}