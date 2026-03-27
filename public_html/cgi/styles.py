THEME = {
    # --- PAGE LAYOUTS ---
    "page_center": "min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8",
    "dashboard_grid": "min-h-screen md:grid md:grid-cols-[260px_1fr]",
    "content_container": "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8",

    # --- CARDS & CONTAINERS ---
    "card_centered": "max-w-md w-full space-y-8 bg-white p-10 rounded-xl shadow-xl border border-gray-100",
    "card_dashboard": "bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mb-6",
    "card_header": "px-6 py-4 border-b border-gray-100 bg-gray-50/50",
    "card_body": "p-6",

    # --- AUCTION GRID (display_auctions.py) ---
    "grid_layout": "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6",
    "auction_card": "group bg-white rounded-xl shadow-sm hover:shadow-md transition border border-gray-200 overflow-hidden flex flex-col h-full",
    "auction_img_placeholder": "h-48 bg-gray-100 flex items-center justify-center text-gray-400",

    # --- TYPOGRAPHY ---
    "h1_center": "text-3xl font-extrabold text-gray-900 tracking-tight text-center",
    "h2_dashboard": "text-2xl font-bold text-gray-900",
    "h3_card": "text-lg font-bold text-gray-800",
    "label": "block text-sm font-medium text-gray-700 mb-1",
    "subtext": "mt-2 text-sm text-gray-600 text-center",
    "price_text": "text-2xl font-bold text-gray-900",

    # --- FORMS & INPUTS ---
    "input": "appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm",
    "select": "block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md",

    # --- BUTTONS ---
    "btn_primary": "w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none cus:ring-indigo-500 transition duration-150 cursor-pointer",
    "btn_sm": "inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indifocus:ring-2 focus:ring-offset-2 fogo-500",

    # --- ALERTS & BADGES ---
    "error_box": "bg-red-50 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded-r",
    "badge_winning": "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800",
    "badge_outbid": "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800",

    # --- TABLES ---
    "table_wrapper": "overflow-x-auto",
    "table": "min-w-full divide-y divide-gray-200",
    "th": "px-6 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
    "td": "px-6 py-4 whitespace-nowrap text-sm text-gray-900",

    # --- SIDEBAR ---
    "sidebar_bg": "bg-[#0b1736] text-blue-50 flex flex-col gap-6 p-6 min-h-screen",
    "nav_link": "flex items-center gap-3 px-3 py-2.5 rounded-lg text-blue-100 hover:bg-white/10 hover:text-white transition",
    "nav_link_active": "flex items-center gap-3 px-3 py-2.5 rounded-lg bg-blue-600 text-white font-medium shadow-md"
}