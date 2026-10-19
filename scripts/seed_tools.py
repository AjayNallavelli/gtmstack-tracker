"""One-time seed of data/tools.json from the 2026-10-19 manual pricing review.
WARNING: re-running overwrites data/tools.json. After launch, edit data/tools.json directly."""
import json
D="2026-10-19"
def T(plan, m=None, a=None, limits="", note=""):
    return {"plan":plan,"monthly_usd":m,"annual_monthly_usd":a,"limits":limits,"note":note}
tools=[]
def add(id,name,website,cat,desc,url,status,tiers,billing="",note="",aff_prog="",extra_cats=()):
    tools.append({"id":id,"name":name,"website":website,"category":cat,"categories":[cat,*extra_cats],
      "description":desc,"pricing_url":url,"date_checked":D,"pricing_status":status,
      "pricing_verified": status in ("public","partial"),
      "billing_note":billing,"verification_note":note,"tiers":tiers,
      "affiliate_url":"","affiliate_program":aff_prog,"featured":False})
SDR="AI SDR agents"; CE="Cold email & engagement"; DATA="Data & enrichment"; DEL="Deliverability & warmup"
# ---- AI SDR
add("11x","11x","https://www.11x.ai",SDR,"AI digital workers (Alice for outbound, Julian for inbound calls) that prospect, write and book meetings across email, voice and chat.",
 "https://www.11x.ai/","contact_sales",[T("Custom",note="No public pricing page (/pricing returns 404); demo required")],
 note="11x.ai/pricing returned HTTP 404 on 2026-10-19; homepage only offers a demo.")
add("artisan","Artisan","https://www.artisan.co",SDR,"AI BDR 'Ava' that finds leads, researches them and runs multichannel outbound from one platform.",
 "https://www.artisan.co/pricing","contact_sales",[T("Custom",note="'Pricing scoped on your plan' — sized to lead volume, mailboxes and dialer seats")],
 note="Pricing page requires a call; no dollar figures published.")
add("aisdr","AiSDR","https://aisdr.com",SDR,"AI SDR that researches prospects, writes personalized email/LinkedIn outreach and handles replies.",
 "https://aisdr.com/pricing/","public",[
  T("Pay as you go",None,None,"$1.50 per person prospected; research, lists and writing included",note="Usage-based, charged daily"),
  T("Per-campaign managed service",None,None,"$149 per campaign (GTM engineer builds one campaign)"),
  T("Fully managed service",2500,None,"AiSDR runs targeting, messaging, replies and reporting")],
 billing="Usage-based self-serve; add-ons: warmed-up mailbox $33")
add("regie","Regie.ai","https://www.regie.ai",SDR,"RegieGO AI prospecting agents: research, enrichment, drafting and sending from your own Gmail/Outlook.",
 "https://www.regie.ai/pricing","public",[
  T("Free",0,0,"250 one-time credits per person, up to 10 people"),
  T("Pro",49,41,"5,000 credits/month (60,000 up front on annual); 1 person"),
  T("Team",150,125,"Per seat; 15,000 credits/seat/month"),
  T("Enterprise",None,None,"Volume credits, SOC 2 / enterprise security",note="Custom")],
 billing="Monthly price shown; annual saves 17%")
add("replyio","Reply.io","https://reply.io",SDR,"Sales engagement platform with email, LinkedIn, calls and SMS plus the Jason AI SDR agent.",
 "https://reply.io/pricing/","public",[
  T("Email Volume",59,49,"From 1,000 active contacts/month; unlimited users & mailboxes",note="Starts-from price; scales with contacts"),
  T("Multichannel",99,89,"Per user; email, LinkedIn, SMS, calls"),
  T("AI SDR Starter",800,500,"From 1,000 active contacts",note="Starts-from"),
  T("AI SDR Growth",2500,1500,"From 5,000 active contacts",note="Starts-from"),
  T("Agency Core",None,210,"Multiple client workspaces",note="Shown as starts from $210/month")],
 billing="Monthly vs annual both shown; LinkedIn automation $69/mo/acct, Calls & SMS $29/mo/acct add-ons", extra_cats=(CE,))
add("amplemarket","Amplemarket","https://www.amplemarket.com",SDR,"AI sales copilot (Duo) combining B2B data, intent signals and multichannel sequences.",
 "https://www.amplemarket.com/pricing","partial",[
  T("Startup",None,600,"2 users included; 27,000 contacts",note="$600/mo on annual term"),
  T("Growth",None,None,"4 users; 140,000 contacts",note="Custom"),
  T("Elite",None,None,"400,000 contacts",note="Custom")],
 billing="Annual term only shown", extra_cats=(DATA,))
add("persana","Persana AI","https://persana.ai",SDR,"AI prospecting agents and signal-based enrichment (Clay-style waterfall) for outbound teams.",
 "https://persana.ai/pricing","public",[
  T("Free",0,0,"50 credits/month"),
  T("Starter",None,68,"24k credits/yr"),
  T("Growth",None,151,"60k credits/yr"),
  T("Pro",None,400,"216k credits/yr; unlimited users; CRM integration")],
 billing="Prices shown billed annually (annual saves 20%); monthly prices not captured", extra_cats=(DATA,))
# ---- Cold email
add("instantly","Instantly","https://instantly.ai",CE,"Cold email at scale: unlimited sending accounts and warmup, lead database (SuperSearch) and AI agents.",
 "https://instantly.ai/pricing","public",[
  T("Outreach Growth",47,37.6,"5,000 emails/mo, 1,000 uploaded contacts, unlimited accounts & warmup"),
  T("Outreach Hypergrowth",97,77.6,"125,000 emails/mo, 25,000 uploaded contacts"),
  T("Outreach Light Speed",358,286.3,"500,000 emails/mo, 100,000 uploaded contacts, SISR private IPs"),
  T("Leads Growth Credits",47,37.6,"1,500-2,000 Instantly credits/mo, 450M+ lead database"),
  T("Leads Supersonic",97,87.3,"5,000-7,500 credits/mo"),
  T("Bundle Starter",94,85,"5,000 emails + 1,500 credits/mo"),
  T("Bundle Scale",194,175,"100,000 emails + 5,000 credits/mo"),
  T("Bundle Agency",555,500,"500,000 emails + 10,000 credits/mo"),
  T("Enterprise",None,None,"500k+ emails, private deliverability network",note="Custom")],
 billing="Monthly and annual both shown", aff_prog="Recurring affiliate, reported 20-40% (not yet joined)", extra_cats=(DEL,))
add("smartlead","Smartlead","https://www.smartlead.ai",CE,"Cold email platform with unlimited mailboxes, auto-warmup, inbox rotation and agency white-label.",
 "https://www.smartlead.ai/pricing","public",[
  T("Base",39,32,"2,000 contacts, 6,000 emails/mo"),
  T("Pro",94,78,"30,000 contacts, 90,000 emails/mo"),
  T("Unlimited Smart",174,None,"Unlimited contacts, 150,000 emails/mo, 50,000 verified emails"),
  T("Unlimited Prime",379,None,"Unlimited contacts, 500,000 emails/mo, 170,000 verified emails")],
 billing="Monthly shown; annual Base $32, Pro $78; verified-prospect-email add-on $59/mo on Base/Pro", aff_prog="Recurring affiliate, reported 15-35% (not yet joined)")
add("lemlist","lemlist","https://www.lemlist.com",CE,"Multichannel outreach (email, LinkedIn, calls) with built-in lead database, lemwarm warmup and AI agents.",
 "https://www.lemlist.com/pricing","public",[
  T("Email",69,55,"Unlimited users & senders, 50,000 emails/mo, 650M+ lead database"),
  T("Multichannel",109,87,"Per user; email + LinkedIn + calls"),
  T("Enterprise",None,None,"",note="Talk to sales")],
 billing="Monthly vs annual (save 20%); data add-on $20/mo for 2k credits, intent signals $29/mo. lemwarm warmup is now bundled into lemlist plans (no standalone price on lemlist.com/lemwarm)", extra_cats=(DEL,))
add("apollo","Apollo.io","https://www.apollo.io",CE,"All-in-one GTM platform: 200M+ contact database, sequences, dialer and AI research.",
 "https://www.apollo.io/pricing","public",[
  T("Free",0,0,"900 credits/seat/yr granted monthly"),
  T("Basic",None,49,"30,000 credits/seat/yr"),
  T("Professional",None,79,"48,000 credits/seat/yr"),
  T("Organization",None,119,"72,000 credits/seat/yr; min 3 seats")],
 billing="Per seat, billed annually (page default); monthly-billing figures not captured. Add-ons: Inbound $119-$639/team/mo, Advanced Dialer $119/team/mo", note="Pricing renders client-side; captured with headless Chrome.", extra_cats=(DATA,))
add("woodpecker","Woodpecker","https://woodpecker.co",CE,"Cold email and LinkedIn outreach priced by contacted prospects, with free warmup and catch-all verification.",
 "https://woodpecker.co/pricing/","partial",[
  T("Cold Email (usage-based)",None,None,"$7.00 per 100 contacted prospects (annual saves 25%); unlimited team members & email accounts",note="Slider-based; no fixed tier"),
  T("LinkedIn add-on",29,None,"Per connected LinkedIn account"),
  T("Agency panel",27,None,"Per active client")],
 billing="Usage-based slider", note="Box fetch showed INR; USD figures read via a US-region fetch.")
add("saleshandy","Saleshandy","https://www.saleshandy.com",CE,"Cold email outreach with unlimited email accounts, warmup and a B2B lead finder.",
 "https://www.saleshandy.com/pricing/","public",[
  T("Starter",41,34,""),T("Pro",99,76,"Most popular"),T("Scale",189,149,"")],
 billing="Monthly vs annual (annual: $408/$912/$1,788 per year); taxes excluded")
add("mailshake","Mailshake","https://mailshake.com",CE,"Cold email and sales engagement with AI copywriter (SHAKESpeare) and phone/LinkedIn tasks.",
 "https://mailshake.com/pricing/","public",[
  T("Starter",29,25,"For businesses starting outreach"),
  T("Email Outreach",49,45,"For teams scaling email outreach"),
  T("Sales Engagement",99,85,"Multichannel")],
 billing="Monthly vs yearly; Data Finder add-on $19/mo, ready-to-use mailboxes $12/mo")
add("snovio","Snov.io","https://snov.io",CE,"Email finder, verifier and drip campaigns with unlimited seats on all plans.",
 "https://snov.io/pricing","public",[
  T("Trial",0,0,"50 credits"),T("Starter",39,None,"1,000 credits/mo"),T("Pro S",99,None,"5,000 credits/mo"),
  T("Pro M",189,None,"20,000 credits/mo"),T("Pro L",369,None,"50,000 credits/mo"),T("Ultra",738,None,"100,000 credits/mo")],
 billing="Monthly; 25% off annual. LinkedIn slots $69/mo each", extra_cats=(DATA,))
add("klenty","Klenty","https://www.klenty.com",CE,"Sales engagement platform with email cadences, dialer and CRM sync.",
 "https://www.klenty.com/pricing/","public",[
  T("Starter",None,50,"Unlimited users/mailboxes; contacts-based"),
  T("Growth",None,70,"Per user; 200 dialer minutes"),
  T("Plus",None,99,"Per user; 1,000 dialer minutes")],
 billing="Billed annually (save up to 20%); Parallel & Power Dialer add-on $45/user/mo")
add("lagrowthmachine","La Growth Machine","https://lagrowthmachine.com",CE,"Multichannel (LinkedIn, email, X, calls) prospecting automation priced per identity.",
 "https://lagrowthmachine.com/pricing/","partial",[
  T("Basic",None,None,"LinkedIn + email; per identity",note="€50/month per identity (EUR shown)"),
  T("Pro",None,None,"LinkedIn, email, calls",note="€100/month per identity"),
  T("Ultimate",None,None,"LinkedIn, email, X, calls; 1,000 leads enriched/mo",note="€150/month per identity")],
 billing="Prices published in EUR only")
add("outreach","Outreach","https://www.outreach.io",CE,"Enterprise sales execution platform with AI agents, sequencing, forecasting and conversation intelligence.",
 "https://www.outreach.io/pricing","contact_sales",[T("Custom",note="Seat-based + consumption AI credits; 'Request pricing'")])
add("salesloft","Salesloft","https://www.salesloft.com",CE,"Revenue orchestration platform (cadences, conversation intelligence, deals).",
 "https://www.salesloft.com/pricing","contact_sales",[T("Custom",note="Pricing page is a 'Talk to Sales' form")])
# ---- Data
add("clay","Clay","https://www.clay.com",DATA,"Spreadsheet-style GTM data platform with 100+ provider waterfalls, AI research agents and CRM sync.",
 "https://www.clay.com/pricing","public",[
  T("Free",0,0,"Unlimited seats & tables; limited credits"),
  T("Launch",185,167,"15,000 actions/mo + 2,500 data credits/mo (starting point)"),
  T("Growth",495,446,"40,000 actions/mo + 6,000 data credits/mo; CRM auto-sync, HTTP API"),
  T("Enterprise",None,None,"",note="Custom, annual commitment")],
 billing="Actions + data credits priced separately; data credits from $0.05 each", aff_prog="Affiliate reported 20% (not yet joined)")
add("zoominfo","ZoomInfo","https://www.zoominfo.com",DATA,"Enterprise B2B contact, company and intent data with GTM workspace.",
 "https://www.zoominfo.com/pricing","contact_sales",[T("Professional / Advanced / Elite",note="All tiers 'Get a demo' — no public prices")])
add("hubspot-breeze","HubSpot Breeze Intelligence (Data Hub)","https://www.hubspot.com/products/data",DATA,"HubSpot's data enrichment (formerly Clearbit) — now packaged in Data Hub with HubSpot Credits.",
 "https://www.hubspot.com/pricing/data","partial",[
  T("Free",0,0,"Up to 2 users; data sync"),
  T("Starter",None,None,"500 HubSpot Credits",note="Shown in INR to our fetcher: ₹585/mo/seat annual, ₹1,670 monthly"),
  T("Professional",None,None,"5,000 HubSpot Credits; 1 core seat",note="₹60,030/mo annual (INR shown)"),
  T("Enterprise",None,None,"",note="₹167,000/mo (INR shown)")],
 billing="Geo-localized; USD not captured (US fetch failed to load pricing widget)",
 note="Clearbit was acquired by HubSpot and became Breeze Intelligence; enrichment now sold via Data Hub + HubSpot Credits.")
add("lusha","Lusha","https://www.lusha.com",DATA,"B2B contact data (emails, direct dials) with Chrome extension, enrichment and intent.",
 "https://www.lusha.com/pricing/","public",[
  T("Free",0,0,"40 credits/month"),
  T("Starter",None,37.45,"4,800 credits/yr, 1 seat"),
  T("Pro",None,52.45,"Bulk enrichment, AI assistant, 5 intent topics"),
  T("Premium",None,299.95,"40,800 credits/yr, 5 seats")],
 billing="Billed yearly (credits upfront)")
add("cognism","Cognism","https://www.cognism.com",DATA,"GDPR-focused B2B data with phone-verified mobile numbers (Diamond Data), strong in EMEA.",
 "https://www.cognism.com/pricing","contact_sales",[T("Grow / Elevate",note="'Get a personalised quote' — no public prices")])
add("seamless","Seamless.AI","https://seamless.ai",DATA,"Real-time search engine for B2B contact info with Chrome extension and buyer intent.",
 "https://seamless.ai/pricing","contact_sales",[T("Free / Pro / Enterprise",note="Pricing page is a 'Pricing Inquiry' form; no dollar figures")])
add("rocketreach","RocketReach","https://rocketreach.co",DATA,"Contact lookup for emails and phone numbers across 700M+ profiles.",
 "https://rocketreach.co/pricing","partial",[
  T("Essentials",None,None,"",note="Localized: ₹9,496 billed annually"),
  T("Pro",None,None,"",note="₹19,086 billed annually"),
  T("Ultimate",None,None,"",note="₹38,173 billed annually"),
  T("Team / Enterprise",None,None,"",note="'Plans start at $6K annually'")],
 billing="Geo-localized pricing; USD per-plan prices not captured")
add("kaspr","Kaspr","https://www.kaspr.io",DATA,"LinkedIn Chrome extension for phone numbers and emails (Cognism-owned), popular in Europe.",
 "https://www.kaspr.io/pricing","public",[
  T("Free",0,0,"15 B2B email, 5 phone, 5 direct email credits"),
  T("Starter",65,49,"Per user; up to 12,000 exports/yr"),
  T("Business",99,79,"Per user")],
 billing="Monthly vs annual; also EUR/GBP")
add("pdl","People Data Labs","https://www.peopledatalabs.com",DATA,"Developer-first person and company data APIs for enrichment and search.",
 "https://www.peopledatalabs.com/pricing","public",[
  T("Free",0,0,"Up to 100 credits/mo; Person APIs, contact data not included"),
  T("Self-Serve",98,None,"Starting at 350 credits/mo; contact data + premium fields"),
  T("Enterprise",None,None,"",note="Custom")],
 billing="Annual saves 20%")
add("hunter","Hunter","https://hunter.io",DATA,"Email finder, verifier and simple cold email sequences; unlimited users on all plans.",
 "https://hunter.io/pricing","public",[
  T("Free",0,0,"50 credits/mo"),T("Starter",49,34,"2,000 credits/mo"),
  T("Growth",149,104,"10,000 credits/mo"),T("Scale",299,209,"25,000 credits/mo"),T("Enterprise",None,None,"",note="Contact sales")],
 billing="Monthly vs yearly (save 30%)", extra_cats=(CE,))
add("fullenrich","FullEnrich","https://fullenrich.com",DATA,"Waterfall enrichment across 15+ providers for work emails and mobile numbers; pay only for found data.",
 "https://fullenrich.com/pricing","public",[
  T("Free trial",0,0,"50 credits"),
  T("Pro",55,None,"1,000 credits/mo at $0.055/credit (slider 500 to 100K+); unlimited users",note="Monthly price computed from per-credit price shown"),
  T("Pro 15K",720,None,"15,000 credits/mo"),
  T("Enterprise",None,None,"",note="Custom")],
 billing="Credit slider; rollover 3 months (monthly) / 12 months (yearly)")
add("findymail","Findymail","https://www.findymail.com",DATA,"Verified email and phone finder with Sales Navigator scraping and CRM enrichment (Datacare).",
 "https://www.findymail.com/pricing/","public",[
  T("Individual",99,None,"'Generous usage'"),T("Team",399,None,"5x more usage"),T("Scale",999,None,"20x more usage"),
  T("Datacare",None,500,"CRM cleanup; priced on CRM size",note="Starting from $500/mo billed annually")],
 billing="Pay yearly = 2 months free", note="Plain HTTP fetch blocked (403); captured with headless Chrome.")
add("prospeo","Prospeo","https://prospeo.io",DATA,"B2B email and mobile finder with 45+ filter search, enrichment API and MCP server.",
 "https://prospeo.io/pricing","public",[
  T("Free",0,0,"100 credits/mo"),T("Starter",49,37,"2,000 credits/mo per user"),
  T("Growth",99,74,"5,000 credits/mo per user; HubSpot & Salesforce"),T("Pro",249,187,"15,000 credits/mo per user")],
 billing="Monthly vs yearly (save 25%)", note="Page is client-rendered; captured via web fetch.")
add("bettercontact","BetterContact","https://bettercontact.rocks",DATA,"Waterfall enrichment across 20+ email and phone providers, credits roll over.",
 "https://bettercontact.rocks/pricing/","public",[
  T("Starter",15,None,"200 credits/mo (20 mobiles or 200 emails)"),T("Pro",49,None,"1,000 credits/mo"),T("Enterprise",799,None,"From $799/mo; high-volume")],
 billing="Monthly; annual = 2 months free")
# ---- Deliverability
add("allegrow","Allegrow","https://www.allegrow.co",DEL,"Email verification (incl. catch-alls) plus domain health and spam-trap protection for GTM teams.",
 "https://www.allegrow.co/pricing","public",[
  T("Free trial",0,0,"Verify up to 1,000 addresses"),T("Starter",99,None,"5,000 contacts/mo verification, 1 mailbox"),
  T("Scale Plus Unlimited",None,1340,"Unlimited verification, HubSpot/Outreach/Salesloft integrations",note="Billed annually"),
  T("API Plan",None,None,"",note="Custom")])
add("warmbox","Warmbox","https://www.warmbox.ai",DEL,"Email warmup service for cold email inboxes.",
 "https://www.warmbox.ai/pricing/","public",[
  T("Solo",19,15,"1 inbox"),T("Start-up",79,69,"3 inboxes"),T("Growth",159,139,"6 inboxes"),T("Custom",None,None,"",note="Contact")],
 billing="Monthly vs yearly")
add("mailreach","MailReach","https://www.mailreach.co",DEL,"Email warmer plus spam/inbox placement tester.",
 "https://www.mailreach.co/pricing","public",[
  T("All-in-One (warmer + spam tests)",25,20,"Per mailbox per month; includes 20 spam test credits")],
 billing="Per-mailbox slider; annual saves 20%")
add("warmy","Warmy","https://www.warmy.io",DEL,"AI email warmup across a 1M+ mailbox network plus deliverability consulting.",
 "https://www.warmy.io/pricing","partial",[T("Plans from",49,None,"Starting price; 1M+ mailbox warmup network",note="'Plans starting from $49/month'")])
add("glockapps","GlockApps","https://glockapps.com",DEL,"Inbox placement testing, DMARC analytics and deliverability monitoring.",
 "https://glockapps.com/pricing/","public",[
  T("Free",0,0,""),T("Essential",None,59,"$708 paid annually"),T("Growth",None,99,"$1,188 paid annually"),T("Enterprise",None,129,"$1,548 paid annually")],
 billing="Annual (save 30%) figures shown")
add("emailguard","EmailGuard","https://emailguard.io",DEL,"Deliverability suite: inbox placement tests, DMARC, blacklist monitoring and domain masking.",
 "https://emailguard.io/pricing","public",[
  T("Free",0,0,""),T("Pro",49,None,"25 domains, 100 email accounts, 300 inbox placement tests"),
  T("Business",129,None,"75 domains, 300 email accounts"),T("Agency",199,None,"200 domains, 1,000 email accounts")])
for t in tools:
    prices=[x for tr in t["tiers"] for x in (tr["monthly_usd"],tr["annual_monthly_usd"]) if x]
    t["starting_price_usd"]=min(prices) if prices else None
    t["fetch_method"]="chrome" if t["id"] in {"apollo","findymail","lusha","rocketreach","11x","hubspot-breeze","seamless","prospeo","fullenrich","amplemarket","artisan"} else "http"
    t["has_free_plan"]=any((tr["monthly_usd"]==0 or tr["annual_monthly_usd"]==0) for tr in t["tiers"])
DISP={'aisdr': '$1.50 per person prospected', 'woodpecker': '$7 per 100 contacted prospects', 'lagrowthmachine': 'from €50/mo per identity (EUR)', 'rocketreach': 'Localized pricing (USD not captured)', 'hubspot-breeze': 'Free tier; paid tiers localized', 'mailreach': '$20–25 per mailbox/mo'}
for t in tools: t["price_display"]=DISP.get(t["id"],"")
json.dump({"generated":D,"tools":tools},open(__import__("pathlib").Path(__file__).resolve().parent.parent/"data"/"tools.json","w"),indent=2,ensure_ascii=False)
print(len(tools), sum(t["pricing_status"]=="public" for t in tools), sum(t["pricing_status"]=="partial" for t in tools), sum(t["pricing_status"]=="contact_sales" for t in tools))
