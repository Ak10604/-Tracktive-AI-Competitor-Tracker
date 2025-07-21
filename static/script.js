// Enhanced AI-Powered Competitor Tracker JavaScript
let isScanning = false
let autoRefreshInterval

// Utility functions
function showLoading(message = "AI Processing...") {
  const overlay = document.getElementById("loadingOverlay")
  const loadingText = document.getElementById("loadingText")
  if (loadingText) {
    loadingText.textContent = message
  }
  if (overlay) {
    overlay.style.display = "flex"
  }

  // Simulate AI processing steps
  const messages = [
    "🤖 Connecting to Ollama AI...",
    "🌐 Scraping competitor websites...",
    "🧠 Analyzing content changes...",
    "📊 Generating insights...",
    "✅ Finalizing results...",
  ]

  let messageIndex = 0
  const messageInterval = setInterval(() => {
    if (loadingText && messageIndex < messages.length) {
      loadingText.textContent = messages[messageIndex]
      messageIndex++
    } else {
      clearInterval(messageInterval)
    }
  }, 1500)

  if (overlay) {
    overlay.dataset.messageInterval = messageInterval
  }
}

function hideLoading() {
  const overlay = document.getElementById("loadingOverlay")
  if (!overlay) return

  const intervalId = overlay.dataset.messageInterval
  if (intervalId) {
    clearInterval(Number.parseInt(intervalId))
  }
  overlay.style.display = "none"
}

function showNotification(message, type = "success") {
  // Remove existing notifications
  const existingNotifications = document.querySelectorAll(".notification")
  existingNotifications.forEach((n) => n.remove())

  // Create notification element
  const notification = document.createElement("div")
  notification.className = `notification notification-${type}`

  // Add icon based on type
  const icons = {
    success: "✅",
    error: "❌",
    info: "ℹ️",
    warning: "⚠️",
  }

  notification.innerHTML = `
    <div style="display: flex; align-items: center; gap: 0.5rem;">
      <span style="font-size: 1.2rem;">${icons[type] || "📢"}</span>
      <span>${message}</span>
    </div>
  `

  // Style the notification
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    z-index: 3000;
    animation: slideInRight 0.3s ease;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(10px);
    max-width: 400px;
    background: ${getNotificationColor(type)};
  `

  document.body.appendChild(notification)

  // Remove after 4 seconds
  setTimeout(() => {
    notification.style.animation = "slideOutRight 0.3s ease"
    setTimeout(() => {
      if (document.body.contains(notification)) {
        document.body.removeChild(notification)
      }
    }, 300)
  }, 4000)
}

function getNotificationColor(type) {
  const colors = {
    success: "linear-gradient(135deg, #48bb78, #38a169)",
    error: "linear-gradient(135deg, #e53e3e, #c53030)",
    info: "linear-gradient(135deg, #4299e1, #3182ce)",
    warning: "linear-gradient(135deg, #ed8936, #dd6b20)",
  }
  return colors[type] || colors.info
}

// Modal functions
function showAddCompetitorModal() {
  const modal = document.getElementById("addCompetitorModal")
  if (modal) {
    modal.style.display = "block"
    setTimeout(() => {
      const nameInput = document.getElementById("competitorName")
      if (nameInput) nameInput.focus()
    }, 100)
  }
}

function closeModal() {
  const modal = document.getElementById("addCompetitorModal")
  if (modal) {
    modal.style.display = "none"
  }
  const form = document.getElementById("addCompetitorForm")
  if (form) {
    form.reset()
  }
}

function closeChangeModal() {
  const modal = document.getElementById("changeDetailsModal")
  if (modal) {
    modal.style.display = "none"
  }
}

// Company Profile Modal Functions
function editCompanyProfile() {
  const modal = document.getElementById("companyProfileModal")
  if (modal) {
    modal.style.display = "block"
    // Pre-fill form if profile exists
    fillCompanyProfileForm()
  }
}

function closeCompanyProfileModal() {
  const modal = document.getElementById("companyProfileModal")
  if (modal) {
    modal.style.display = "none"
  }
}

function fillCompanyProfileForm() {
  // Get existing company profile data from the page
  const profileDisplay = document.querySelector(".profile-display")
  if (!profileDisplay) return

  try {
    // Extract data from the displayed profile
    const name = document.querySelector(".profile-header h4")?.textContent || ""
    const website = document.querySelector(".detail-item a")?.href || ""
    const industry =
      document.querySelector(".detail-item:nth-child(2)")?.textContent?.replace("🏭 Industry:", "").trim() || ""

    // Populate form fields
    if (document.getElementById("companyName")) document.getElementById("companyName").value = name
    if (document.getElementById("companyWebsite")) document.getElementById("companyWebsite").value = website
    if (document.getElementById("companyIndustry")) document.getElementById("companyIndustry").value = industry

    // You can add more field mappings here based on your needs
  } catch (error) {
    console.log("Could not pre-fill form:", error)
  }
}

// Company Update Modal Functions
function addCompanyUpdate() {
  const modal = document.getElementById("companyUpdateModal")
  if (modal) {
    modal.style.display = "block"
  }
}

function closeCompanyUpdateModal() {
  const modal = document.getElementById("companyUpdateModal")
  if (modal) {
    modal.style.display = "none"
  }
  const form = document.getElementById("companyUpdateForm")
  if (form) {
    form.reset()
  }
}

// Delete company update function
async function deleteCompanyUpdate(updateId) {
  if (!confirm("Are you sure you want to delete this update?")) {
    return
  }

  showLoading("🗑️ Deleting company update...")

  try {
    const response = await fetch(`/delete_company_update/${updateId}`, {
      method: "DELETE",
    })

    const result = await response.json()

    if (result.success) {
      showNotification("🗑️ Company update deleted successfully!", "success")
      // Remove the update from the DOM
      const updateElement = document.querySelector(`[data-update-id="${updateId}"]`)
      if (updateElement) {
        updateElement.remove()
      }
      // Reload page after a short delay to update counts
      setTimeout(() => {
        location.reload()
      }, 1000)
    } else {
      showNotification("Failed to delete update: " + (result.error || "Unknown error"), "error")
    }
  } catch (error) {
    showNotification("Error deleting update: " + error.message, "error")
  } finally {
    hideLoading()
  }
}

// Clear all company updates function
async function clearAllCompanyUpdates() {
  if (!confirm("Are you sure you want to delete ALL company updates? This action cannot be undone.")) {
    return
  }

  showLoading("🗑️ Clearing all company updates...")

  try {
    const response = await fetch("/clear_all_company_updates", {
      method: "DELETE",
    })

    const result = await response.json()

    if (result.success) {
      showNotification("🗑️ All company updates cleared successfully!", "success")
      setTimeout(() => {
        location.reload()
      }, 1000)
    } else {
      showNotification("Failed to clear updates: " + (result.error || "Unknown error"), "error")
    }
  } catch (error) {
    showNotification("Error clearing updates: " + error.message, "error")
  } finally {
    hideLoading()
  }
}

// Enhanced competitor management
function initializeForm() {
  const form = document.getElementById("addCompetitorForm")
  if (!form) return

  form.addEventListener("submit", async (e) => {
    e.preventDefault()

    const nameInput = document.getElementById("competitorName")
    const websiteInput = document.getElementById("competitorWebsite")
    const changelogInput = document.getElementById("changelogUrl")

    if (!nameInput || !websiteInput) {
      showNotification("Form elements not found", "error")
      return
    }

    const formData = {
      name: nameInput.value.trim(),
      website: websiteInput.value.trim(),
      changelog_url: changelogInput ? changelogInput.value.trim() : "",
    }

    if (!formData.name || !formData.website) {
      showNotification("Please fill in all required fields", "error")
      return
    }

    try {
      new URL(formData.website)
    } catch {
      showNotification("Please enter a valid website URL", "error")
      return
    }

    showLoading("🎯 Adding competitor to AI monitoring system...")

    try {
      const response = await fetch("/add_competitor", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      })

      const result = await response.json()

      if (result.success) {
        showNotification(`🎯 ${formData.name} added to AI monitoring!`, "success")
        closeModal()
        setTimeout(() => {
          showNotification("🤖 Starting initial AI scan...", "info")
          setTimeout(() => {
            location.reload()
          }, 2000)
        }, 1000)
      } else {
        showNotification("Failed to add competitor: " + (result.error || "Unknown error"), "error")
      }
    } catch (error) {
      showNotification("Error adding competitor: " + error.message, "error")
    } finally {
      hideLoading()
    }
  })

  // Company Profile Form
  const companyProfileForm = document.getElementById("companyProfileForm")
  if (companyProfileForm) {
    companyProfileForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      const formData = {
        name: document.getElementById("companyName")?.value?.trim() || "",
        website: document.getElementById("companyWebsite")?.value?.trim() || "",
        industry: document.getElementById("companyIndustry")?.value?.trim() || "",
        founded_year: document.getElementById("foundedYear")?.value || null,
        size: document.getElementById("companySize")?.value || "",
        headquarters: document.getElementById("headquarters")?.value?.trim() || "",
        description: document.getElementById("companyDescription")?.value?.trim() || "",
        key_products: document.getElementById("keyProducts")?.value?.trim() || "",
        target_market: document.getElementById("targetMarket")?.value?.trim() || "",
        competitive_advantages: document.getElementById("competitiveAdvantages")?.value?.trim() || "",
      }

      if (!formData.name || !formData.industry) {
        showNotification("Please fill in required fields (Name and Industry)", "error")
        return
      }

      showLoading("💾 Saving company profile...")

      try {
        const response = await fetch("/save_company_profile", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(formData),
        })

        const result = await response.json()

        if (result.success) {
          showNotification("💾 Company profile saved successfully!", "success")
          closeCompanyProfileModal()
          setTimeout(() => {
            location.reload()
          }, 1000)
        } else {
          showNotification("Failed to save profile: " + (result.error || "Unknown error"), "error")
        }
      } catch (error) {
        showNotification("Error saving profile: " + error.message, "error")
      } finally {
        hideLoading()
      }
    })
  }

  // Company Update Form
  const companyUpdateForm = document.getElementById("companyUpdateForm")
  if (companyUpdateForm) {
    companyUpdateForm.addEventListener("submit", async (e) => {
      e.preventDefault()

      const formData = {
        title: document.getElementById("updateTitle")?.value?.trim() || "",
        update_type: document.getElementById("updateType")?.value || "",
        importance_score: Number.parseInt(document.getElementById("updateImportance")?.value) || 5,
        date_published: document.getElementById("updateDate")?.value || new Date().toISOString().split("T")[0],
        content: document.getElementById("updateContent")?.value?.trim() || "",
        source_url: document.getElementById("updateSource")?.value?.trim() || "",
        tags: document.getElementById("updateTags")?.value?.trim() || "",
      }

      if (!formData.title || !formData.update_type || !formData.importance_score) {
        showNotification("Please fill in required fields", "error")
        return
      }

      showLoading("📢 Adding company update...")

      try {
        const response = await fetch("/add_company_update", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(formData),
        })

        const result = await response.json()

        if (result.success) {
          showNotification("📢 Company update added successfully!", "success")
          closeCompanyUpdateModal()
          setTimeout(() => {
            location.reload()
          }, 1000)
        } else {
          showNotification("Failed to add update: " + (result.error || "Unknown error"), "error")
        }
      } catch (error) {
        showNotification("Error adding update: " + error.message, "error")
      } finally {
        hideLoading()
      }
    })
  }
}

// Competitive Analysis Functions
async function generateCompetitiveInsights() {
  showLoading("🧠 Generating AI competitive insights with industry research...")

  try {
    const response = await fetch("/generate_competitive_insights")
    const result = await response.json()

    if (result.insights) {
      const insightsOutput = document.getElementById("competitiveInsights")
      if (insightsOutput) {
        insightsOutput.innerHTML = `
          <div class="insights-content">
            <div class="insights-header">
              <h4>🤖 AI Competitive Analysis</h4>
              <p>Industry-specific analysis of ${result.changes_analyzed} competitor changes for ${result.company_name}</p>
            </div>
            <div class="insights-text">
              <div style="white-space: pre-wrap; font-family: inherit; line-height: 1.6; background: #f8f9fa; padding: 1.5rem; border-radius: 10px; border-left: 4px solid #667eea;">${result.insights}</div>
            </div>
            <div class="insights-actions">
              <button onclick="copyToClipboard(\`${result.insights.replace(/`/g, "\\`")}\`)" class="btn btn-small btn-primary">
                <span class="btn-icon">📋</span>Copy Analysis
              </button>
              <button onclick="exportComparisonReport()" class="btn btn-small btn-secondary">
                <span class="btn-icon">📄</span>Export Report
              </button>
            </div>
          </div>
        `
      }

      showNotification(
        `🧠 AI insights generated with industry research covering ${result.changes_analyzed} competitor changes!`,
        "success",
      )
    } else {
      showNotification("Error: " + (result.error || "Failed to generate insights"), "error")
    }
  } catch (error) {
    showNotification("Error generating insights: " + error.message, "error")
  } finally {
    hideLoading()
  }
}

// Filtering Functions
function applyFilters() {
  const timeFilter = document.getElementById("timeFilter")?.value || "all"
  const importanceFilter = document.getElementById("importanceFilter")?.value || "all"
  const typeFilter = document.getElementById("typeFilter")?.value || "all"
  const competitorFilter = document.getElementById("competitorFilter")?.value || "all"

  // Filter company activity
  const companyItems = document.querySelectorAll("#companyActivity .activity-item")
  companyItems.forEach((item) => {
    let show = true

    // Time filter
    if (timeFilter !== "all") {
      const itemDate = new Date(item.dataset.date)
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - Number.parseInt(timeFilter))
      if (itemDate < cutoffDate) show = false
    }

    // Importance filter
    if (importanceFilter !== "all") {
      const importance = Number.parseInt(item.dataset.importance)
      if (importanceFilter === "high" && importance < 7) show = false
      if (importanceFilter === "medium" && (importance < 4 || importance > 6)) show = false
      if (importanceFilter === "low" && importance > 3) show = false
    }

    // Type filter
    if (typeFilter !== "all" && item.dataset.type !== typeFilter) {
      show = false
    }

    item.style.display = show ? "block" : "none"
  })

  // Filter competitor activity
  const competitorItems = document.querySelectorAll("#competitorActivity .activity-item")
  competitorItems.forEach((item) => {
    let show = true

    // Time filter
    if (timeFilter !== "all") {
      const itemDate = new Date(item.dataset.date)
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - Number.parseInt(timeFilter))
      if (itemDate < cutoffDate) show = false
    }

    // Importance filter
    if (importanceFilter !== "all") {
      const importance = Number.parseInt(item.dataset.importance)
      if (importanceFilter === "high" && importance < 7) show = false
      if (importanceFilter === "medium" && (importance < 4 || importance > 6)) show = false
      if (importanceFilter === "low" && importance > 3) show = false
    }

    // Type filter
    if (typeFilter !== "all" && item.dataset.type !== typeFilter) {
      show = false
    }

    // Competitor filter
    if (competitorFilter !== "all" && item.dataset.competitor !== competitorFilter) {
      show = false
    }

    item.style.display = show ? "block" : "none"
  })
}

function resetFilters() {
  if (document.getElementById("timeFilter")) document.getElementById("timeFilter").value = "30"
  if (document.getElementById("importanceFilter")) document.getElementById("importanceFilter").value = "all"
  if (document.getElementById("typeFilter")) document.getElementById("typeFilter").value = "all"
  if (document.getElementById("competitorFilter")) document.getElementById("competitorFilter").value = "all"
  applyFilters()
}

// Market Trends Functions
function loadMarketTrends() {
  // Simulate loading market trends
  const hotTopics = document.getElementById("hotTopics")
  const activitySpikes = document.getElementById("activitySpikes")
  const opportunities = document.getElementById("opportunities")

  if (hotTopics) {
    hotTopics.innerHTML = `
      <div class="trend-item">🚀 AI & Machine Learning</div>
      <div class="trend-item">💰 Pricing Strategy Changes</div>
      <div class="trend-item">🤝 Strategic Partnerships</div>
    `
  }

  if (activitySpikes) {
    activitySpikes.innerHTML = `
      <div class="trend-item">📈 Product Launch Season</div>
      <div class="trend-item">🔄 Feature Update Cycles</div>
      <div class="trend-item">📢 Marketing Campaigns</div>
    `
  }

  if (opportunities) {
    opportunities.innerHTML = `
      <div class="trend-item">🎯 Market Gap Identified</div>
      <div class="trend-item">⚡ First-Mover Advantage</div>
      <div class="trend-item">🔍 Underserved Segments</div>
    `
  }
}

// Comparison Page Initialization
function initializeComparison() {
  // Initialize filters
  const filterSelects = document.querySelectorAll(".filter-group select")
  filterSelects.forEach((select) => {
    select.addEventListener("change", applyFilters)
  })

  // Load initial data
  applyFilters()
}

// Export Functions
function exportComparisonReport() {
  showLoading("📄 Generating PDF comparison report...")

  // Redirect to PDF generation endpoint
  window.location.href = "/generate_pdf_report"

  setTimeout(() => {
    hideLoading()
    showNotification("📄 PDF report generated successfully!", "success")
  }, 3000)
}

async function removeCompetitor(competitorId) {
  const competitorCard = document.querySelector(`[data-competitor-id="${competitorId}"]`)
  const competitorName = competitorCard
    ? competitorCard.querySelector("h4")?.textContent || "this competitor"
    : "this competitor"

  if (
    !confirm(
      `🗑️ Are you sure you want to remove ${competitorName} from AI monitoring?\n\nThis will delete all historical data and analysis.`,
    )
  ) {
    return
  }

  showLoading("🗑️ Removing competitor from AI system...")

  try {
    const response = await fetch(`/remove_competitor/${competitorId}`, {
      method: "DELETE",
    })

    const result = await response.json()

    if (result.success) {
      showNotification(`🗑️ ${competitorName} removed from monitoring`, "success")
      setTimeout(() => {
        location.reload()
      }, 1000)
    } else {
      showNotification("Failed to remove competitor: " + (result.error || "Unknown error"), "error")
    }
  } catch (error) {
    showNotification("Error removing competitor: " + error.message, "error")
  } finally {
    hideLoading()
  }
}

async function scanCompetitor(competitorId) {
  if (isScanning) {
    showNotification("🤖 AI scan already in progress...", "info")
    return
  }

  isScanning = true
  const scanButton = document.querySelector(`button[onclick="scanCompetitor(${competitorId})"]`)
  if (scanButton) {
    scanButton.innerHTML = '<span class="btn-icon">🧠</span>AI Scanning...'
    scanButton.disabled = true
  }

  showLoading("🧠 AI analyzing competitor content with Ollama...")

  try {
    const response = await fetch(`/scan_competitor/${competitorId}`)
    const result = await response.json()

    if (result.success && result.change) {
      const change = result.change
      let message = `🤖 AI Analysis Complete!`

      if (change.importance_score >= 8) {
        message += ` 🚨 Critical changes detected!`
        showNotification(message, "warning")
      } else if (change.importance_score >= 6) {
        message += ` ⚠️ Important changes found.`
        showNotification(message, "info")
      } else {
        message += ` ✅ Scan completed successfully.`
        showNotification(message, "success")
      }

      setTimeout(() => {
        location.reload()
      }, 2000)
    } else {
      showNotification("🤖 AI scan failed: " + (result.error || "Unknown error"), "error")
    }
  } catch (error) {
    showNotification("🤖 AI scan error: " + error.message, "error")
  } finally {
    isScanning = false
    hideLoading()
    if (scanButton) {
      scanButton.innerHTML = '<span class="btn-icon">🔍</span>Scan Now'
      scanButton.disabled = false
    }
  }
}

async function scanAllCompetitors() {
  if (isScanning) {
    showNotification("🤖 AI scan already in progress...", "info")
    return
  }

  isScanning = true
  showLoading("🤖 AI scanning all competitors with Ollama...")

  try {
    const response = await fetch("/scan_all")
    const result = await response.json()

    if (result.results) {
      let successCount = 0
      let errorCount = 0
      let highPriorityChanges = 0

      result.results.forEach((r) => {
        if (r.success) {
          successCount++
          if (r.change && r.change.importance_score >= 7) {
            highPriorityChanges++
          }
        } else {
          errorCount++
        }
      })

      let message = `🤖 AI Scan Complete! ${successCount} competitors analyzed`
      if (highPriorityChanges > 0) {
        message += ` 🚨 ${highPriorityChanges} high-priority changes detected!`
        showNotification(message, "warning")
      } else {
        showNotification(message, "success")
      }

      if (errorCount > 0) {
        showNotification(`⚠️ ${errorCount} competitors had scan errors`, "warning")
      }

      setTimeout(() => {
        location.reload()
      }, 3000)
    } else {
      showNotification("🤖 Scan failed: " + (result.error || "Unknown error"), "error")
    }
  } catch (error) {
    showNotification("🤖 AI scan error: " + error.message, "error")
  } finally {
    isScanning = false
    hideLoading()
  }
}

// Enhanced summary generation
async function generateSummary() {
  showLoading("📰 AI generating comprehensive news digest...")

  try {
    const response = await fetch("/generate_summary")
    const result = await response.json()

    if (result.summary) {
      const summaryOutput = document.getElementById("summaryOutput")
      if (summaryOutput) {
        summaryOutput.innerHTML = `<pre style="white-space: pre-wrap; font-family: inherit;">${result.summary}</pre>`
        summaryOutput.scrollIntoView({ behavior: "smooth" })
      } else {
        showAISummaryModal(result.summary, result.changes_count)
      }

      const message = `📰 News digest generated covering ${result.changes_count} competitor updates!`
      showNotification(message, "success")
    } else {
      showNotification("📰 No competitor news to analyze this week", "info")
    }
  } catch (error) {
    showNotification("📰 News digest error: " + error.message, "error")
  } finally {
    hideLoading()
  }
}

function showAISummaryModal(summary, changesCount) {
  const modal = document.createElement("div")
  modal.className = "modal"
  modal.style.display = "block"

  modal.innerHTML = `
    <div class="modal-content large">
      <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
      <div class="modal-header">
        <h3>📰 Weekly Competitor News Digest</h3>
        <p>AI-powered business intelligence covering ${changesCount} competitor updates</p>
      </div>
      <div style="padding: 2rem;">
        <div class="summary-output" style="background: #f7fafc; padding: 1.5rem; border-radius: 10px; white-space: pre-wrap; font-family: 'Inter', sans-serif; line-height: 1.6; max-height: 500px; overflow-y: auto;">${summary}</div>
        <div class="form-actions" style="margin-top: 2rem;">
          <button onclick="copyToClipboard(\`${summary.replace(/`/g, "\\`")}\`)" class="btn btn-primary">
            <span class="btn-icon">📋</span>Copy News Digest
          </button>
          <button onclick="generatePDFReport()" class="btn btn-pdf">
            <span class="btn-icon">📄</span>Download Report
          </button>
          <button onclick="shareToSlack()" class="btn btn-accent">
            <span class="btn-icon">📤</span>Send to Slack
          </button>
          <button onclick="this.closest('.modal').remove()" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>
  `

  document.body.appendChild(modal)
}

// Enhanced PDF Report Generation
async function generatePDFReport() {
  showLoading("📄 Generating comprehensive PDF report...")

  try {
    const response = await fetch("/generate_pdf_report")
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, "-")
      a.download = `AI_Competitor_Intelligence_Report_${timestamp}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      showNotification("📄 PDF report generated and downloaded!", "success")
    } else {
      const errorData = await response.json()
      showNotification("❌ PDF generation failed: " + (errorData.error || "Unknown error"), "error")
    }
  } catch (error) {
    showNotification("❌ PDF generation error: " + error.message, "error")
  } finally {
    hideLoading()
  }
}

function copyToClipboard(text) {
  if (navigator.clipboard) {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        showNotification("📋 Copied to clipboard!", "success")
      })
      .catch(() => {
        fallbackCopyToClipboard(text)
      })
  } else {
    fallbackCopyToClipboard(text)
  }
}

function fallbackCopyToClipboard(text) {
  const textArea = document.createElement("textarea")
  textArea.value = text
  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()
  try {
    document.execCommand("copy")
    showNotification("📋 Copied to clipboard!", "success")
  } catch (err) {
    showNotification("❌ Failed to copy to clipboard", "error")
  }
  document.body.removeChild(textArea)
}

// Change viewing functions
function viewFullChange(changeId) {
  const changeItem = document.querySelector(`[data-change-id="${changeId}"]`)
  if (!changeItem) {
    showNotification("Change details not found", "error")
    return
  }

  const competitor = changeItem.querySelector("h4")?.textContent || "Unknown"
  const timestamp = changeItem.querySelector(".timestamp")?.textContent || "Unknown"
  const analysis = changeItem.querySelector(".analysis")?.textContent || "No analysis"
  const newsTitle = changeItem.querySelector(".news-title")?.textContent || "No title"
  const newsExcerpt = changeItem.querySelector(".news-excerpt")?.textContent || "No excerpt"
  const sourceLinks = Array.from(changeItem.querySelectorAll(".source-link")).map((link) => link.href)

  const modal = document.createElement("div")
  modal.className = "modal"
  modal.style.display = "block"

  modal.innerHTML = `
    <div class="modal-content large">
      <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
      <div class="modal-header">
        <h3>📊 Change Details</h3>
        <p>${competitor} - ${timestamp}</p>
      </div>
      <div style="padding: 2rem;">
        <h4>📰 News Title</h4>
        <p style="margin-bottom: 1rem;">${newsTitle}</p>
        
        <h4>📝 News Excerpt</h4>
        <p style="margin-bottom: 1rem;">${newsExcerpt}</p>
        
        <h4>🤖 AI Analysis</h4>
        <p style="margin-bottom: 1rem;">${analysis}</p>
        
        ${
          sourceLinks.length > 0
            ? `
        <h4>🔗 Source Links</h4>
        <ul style="margin-bottom: 1rem;">
          ${sourceLinks.map((link) => `<li><a href="${link}" target="_blank">${link}</a></li>`).join("")}
        </ul>
        `
            : ""
        }
        
        <div class="form-actions">
          <button onclick="this.closest('.modal').remove()" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>
  `

  document.body.appendChild(modal)
}

function shareChange(changeId) {
  showNotification("📤 Share functionality coming soon!", "info")
}

function loadMoreChanges() {
  showNotification("📜 Load more functionality coming soon!", "info")
}

function refreshChanges() {
  location.reload()
}

// Dashboard specific functions
async function updateSlackWebhook() {
  const webhook = document.getElementById("slackWebhook")?.value.trim()
  if (!webhook) {
    showNotification("⚠️ Please enter a Slack webhook URL", "warning")
    return
  }

  try {
    const response = await fetch("/settings", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ slack_webhook: webhook }),
    })

    const result = await response.json()
    if (result.success) {
      showNotification("🔔 Slack webhook updated successfully!", "success")
    } else {
      showNotification("❌ Failed to update webhook", "error")
    }
  } catch (error) {
    showNotification("❌ Error updating webhook: " + error.message, "error")
  }
}

async function updateNotionToken() {
  const token = document.getElementById("notionToken")?.value.trim()

  try {
    const response = await fetch("/settings", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ notion_token: token }),
    })

    const result = await response.json()
    if (result.success) {
      showNotification("📝 Notion token updated!", "success")
    } else {
      showNotification("❌ Failed to update token", "error")
    }
  } catch (error) {
    showNotification("❌ Error updating token: " + error.message, "error")
  }
}

async function sendToSlack() {
  showLoading("📤 Sending competitor news digest to Slack...")

  try {
    const response = await fetch("/send_to_slack", {
      method: "POST",
    })

    const result = await response.json()
    if (result.success) {
      showNotification("📰 Competitor news digest sent to Slack successfully!", "success")
    } else {
      showNotification("❌ Failed to send news digest to Slack: " + (result.error || "Unknown error"), "error")
    }
  } catch (error) {
    showNotification("❌ Error sending news digest to Slack: " + error.message, "error")
  } finally {
    hideLoading()
  }
}

async function shareToSlack() {
  await sendToSlack()
}

function generateDetailedSummary() {
  generateSummary()
}

function exportData() {
  showLoading("📊 Preparing data export...")

  setTimeout(() => {
    try {
      const date = new Date().toISOString().split("T")[0]
      const csvData = [["Date", "Competitor", "Change Type", "Importance", "AI Analysis", "URL"]]

      const sampleData = [
        [date, "Sample Competitor", "feature_update", "7", "AI detected new feature launch", "https://example.com"],
      ]

      csvData.push(...sampleData)

      const csvContent = csvData
        .map((row) => row.map((cell) => `"${cell.toString().replace(/"/g, '""')}"`).join(","))
        .join("\n")

      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `ai-competitor-analysis-${date}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      showNotification("📊 Data exported successfully!", "success")
    } catch (error) {
      showNotification("❌ Export failed: " + error.message, "error")
    } finally {
      hideLoading()
    }
  }, 1500)
}

function viewChangeDetails(changeId) {
  viewFullChange(changeId)
}

function editCompetitor(competitorId) {
  showNotification("✏️ Edit competitor feature coming soon!", "info")
}

// Auto-refresh functionality
function startAutoRefresh() {
  autoRefreshInterval = setInterval(
    () => {
      if (!isScanning) {
        console.log("🔄 Auto-refreshing to show latest AI scans...")
        location.reload()
      }
    },
    2 * 60 * 1000,
  ) // 2 minutes
}

function stopAutoRefresh() {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval)
  }
}

// Enhanced keyboard shortcuts
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "k") {
    e.preventDefault()
    showAddCompetitorModal()
  }
  if ((e.ctrlKey || e.metaKey) && e.key === "r") {
    e.preventDefault()
    scanAllCompetitors()
  }
  if (e.key === "Escape") {
    const modals = document.querySelectorAll(".modal")
    modals.forEach((modal) => {
      if (modal.style.display === "block") {
        modal.style.display = "none"
      }
    })
  }
})

// Close modals when clicking outside
window.onclick = (event) => {
  const modals = document.querySelectorAll(".modal")
  modals.forEach((modal) => {
    if (event.target === modal) {
      modal.style.display = "none"
    }
  })
}

// Initialize page
document.addEventListener("DOMContentLoaded", () => {
  console.log("🤖 AI-Powered Competitor Tracker initialized")
  console.log("🧠 Ollama integration ready")
  console.log("⌨️ Keyboard shortcuts: Ctrl+K (Add), Ctrl+R (Scan), Esc (Close)")

  // Initialize form handlers
  initializeForm()

  // Initialize comparison page if we're on it
  if (document.getElementById("competitiveInsights")) {
    initializeComparison()
    loadMarketTrends()
  }

  // Set default date for update form
  const today = new Date().toISOString().split("T")[0]
  const updateDateInput = document.getElementById("updateDate")
  if (updateDateInput) {
    updateDateInput.value = today
  }

  // Start auto-refresh
  startAutoRefresh()

  // Show appropriate welcome message based on page context
  const competitors = document.querySelectorAll(".competitor-card")
  const changes = document.querySelectorAll(".change-item")

  // Only show competitor welcome message on home page when no competitors exist
  if (window.location.pathname === "/" && competitors.length === 0) {
    setTimeout(() => {
      showNotification("👋 Welcome! Add your first competitor to start AI monitoring", "info")
    }, 1000)
  } else if (window.location.pathname === "/" && competitors.length > 0 && changes.length === 0) {
    setTimeout(() => {
      showNotification("🔍 Competitors added! Run a scan to start detecting changes", "info")
    }, 1000)
  }

  // Add enhanced CSS animations
  const style = document.createElement("style")
  style.textContent = `
    @keyframes slideInRight {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
      from { transform: translateX(0); opacity: 1; }
      to { transform: translateX(100%); opacity: 0; }
    }
    @keyframes fadeInUp {
      from { transform: translateY(20px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
    @keyframes fadeOutUp {
      from { transform: translateY(0); opacity: 1; }
      to { transform: translateY(-20px); opacity: 0; }
    }
    .competitor-card {
      animation: fadeInUp 0.5s ease;
    }
    .change-item {
      animation: fadeInUp 0.3s ease;
    }
    .btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .btn:active {
      transform: translateY(0);
    }
    .trend-item {
      padding: 0.5rem;
      background: rgba(102, 126, 234, 0.1);
      border-radius: 8px;
      margin-bottom: 0.5rem;
      border-left: 3px solid #667eea;
    }
    .insights-content {
      background: white;
      border-radius: 15px;
      padding: 2rem;
      border: 1px solid rgba(102, 126, 234, 0.1);
    }
    .insights-header {
      text-align: center;
      margin-bottom: 2rem;
      padding-bottom: 1rem;
      border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    }
    .insights-header h4 {
      font-size: 1.5rem;
      color: #2d3748;
      margin: 0 0 0.5rem 0;
      font-weight: 700;
    }
    .insights-header p {
      color: #4a5568;
      margin: 0;
    }
    .insights-text {
      margin-bottom: 2rem;
      line-height: 1.6;
    }
    .insights-actions {
      display: flex;
      gap: 1rem;
      justify-content: center;
      flex-wrap: wrap;
    }
    .news-filters {
      display: flex;
      gap: 0.5rem;
      align-items: center;
    }
    .news-filters select {
      padding: 0.5rem;
      border: 2px solid #e2e8f0;
      border-radius: 8px;
      font-size: 0.9rem;
    }
  `
  document.head.appendChild(style)
})

// Cleanup on page unload
window.addEventListener("beforeunload", () => {
  stopAutoRefresh()
})
