from playwright.async_api import async_playwright, expect
import asyncio
import unicodedata
from telegram_bot.state import wait_for_product_selection, wait_for_order_confirmation
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def clean_text(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')


async def safe_goto(page, url, retries=3, timeout=60000):
    for attempt in range(1, retries + 1):
        try:
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            return True
        except Exception as e:
            print(f"⚠️ Attempt {attempt}: Failed to load page ({e})")
            if attempt == retries:
                raise e
            await asyncio.sleep(3)  # wait before retry
    return False


async def run(parsed_list, send_update=None, auto_address=True, user_id=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://alfatah.pk/", wait_until="domcontentloaded")
        await page.wait_for_selector("span.new-address-span", timeout=20000)

        if auto_address:
            await _send("📍 Setting address automatically...", send_update)

            try:
                await page.evaluate("window.scrollTo(0, 0)")  # Scroll to top
                await page.mouse.wheel(0, -10000)  # Extra scroll up just in case
                await asyncio.sleep(1)  # Let UI settle
                await page.locator("span.new-address-span").click()

                await page.wait_for_selector("div.add-new-address", timeout=5000)
                await page.locator("div.add-new-address").click()

                await page.wait_for_selector("input[placeholder='Select City']", timeout=5000)
                await page.locator("input[placeholder='Select City']").fill("Lahore")
                await asyncio.sleep(1)
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("Enter")

                await page.wait_for_selector("input[placeholder='Search for a location']", timeout=5000)
                await page.locator("input[placeholder='Search for a location']").fill("DHA Phase 5 Lahore")
                await page.locator("button:has-text('Search')").click()

                await page.wait_for_timeout(2000)
                await page.wait_for_selector(".tpl-search-results li", timeout=5000)
                await page.locator(".tpl-search-results li").first.click()
                await page.wait_for_timeout(2000)

                await page.wait_for_selector("div.confirm_location_button", timeout=10000)
                await page.locator("div.confirm_location_button").click()

                await page.wait_for_selector("input[placeholder='Apartment, suite, etc.']", timeout=5000)
                await page.locator("input[placeholder='Apartment, suite, etc.']").fill("123B")
                await page.locator("input#map_area").fill("Street 3")

                await page.click("button:has-text('Set Location')")
                await _send("✅ Address set successfully.", send_update)

            except Exception as e:
                await _send(f"❌ Failed to set address: {e}", send_update)
                return
        else:
            await _send("🌐 Website loaded. Set the address manually and press Enter to continue...", send_update)
            input("Set the address manually and press Enter to continue...")

        # Shopping loop continues here...
        # (the rest of your existing run() code follows after this)

        # ⬇️ KEEP ALL YOUR SEARCH + ADD TO CART + CHECKOUT logic here ⬇️

        for item in parsed_list:
            unit = item.get("unit")
            unit_str = f" {unit}" if unit else ""
            search_msg = f"🔍 Searching for: {clean_text(item['product'])} ({item['quantity']}{unit_str})"
            print(search_msg)
            await _send(search_msg, send_update)

            results = await get_top_products(page, clean_text(item["product"]), count=3)

            if not results:
                await _send("⚠️ No products found.", send_update)
                continue

            # Send product images first
            for i, product in enumerate(results[:3]):
                # Send each product photo with its own inline button
                keyboard = [
                    [InlineKeyboardButton("Select this", callback_data=f"select_{i}")]
                ]
                await send_update(
                    photo_url=product["image"],
                    caption=f"{product['title']}\nPrice: {product['price']}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

            selected = await wait_for_product_selection(user_id)
            # print(f"📥 Got user selection: {selected}")

            if selected and selected.startswith("select_"):
                index = int(selected.split("_")[1])  # Extract selected index
                product_element = page.locator("#ProductGridContainer .product-card").nth(index)
                try:
                    quantity = item.get("quantity", 1)
                    plus_button = product_element.locator(".product-plus")
                    qty_display = product_element.locator(".product-quantity-number")

                    for i in range(quantity):
                        await plus_button.click()
                        await expect(qty_display).to_have_text(str(i + 1), timeout=5000)
                        msg = f"🛒 Quantity now: {i + 1}"
                        print(msg)
                        await _send(msg, send_update)

                except Exception as e:
                    error = f"❌ Failed to add {item['product']} to cart: {e}"
                    print(error)
                    await _send(error, send_update)

            elif selected == "show_all":
                all_results_link = f"https://alfatah.pk/search?q={item['product'].replace(' ', '+')}"
                await _send(f"🔗 [View all results]({all_results_link})", send_update)
                await _send("❌ Skipping this product...", send_update)
                continue

        await proceed_to_checkout(page, send_update=send_update, user_id=user_id)

    # print("\n✅ Done. Press Enter to close browser...")
    # await _send("✅ Done. You can now close the browser.", send_update)
    # await browser.close()


# 🔍 Product search
async def get_top_products(page, product_name="milk", count=3):

    # # 🧹 Try closing any open search modal
    # try:
    #     modal_close_button = page.locator("button.modal__close-button").first
    #     if await modal_close_button.is_visible():
    #         await modal_close_button.click()
    #         await page.wait_for_selector("div.search-modal[aria-hidden='true']", timeout=5000)
    #         await page.wait_for_timeout(1000)  # Give UI a bit to settle
    # except Exception as e:
    #     print("⚠️ No open modal to close or failed to close it:", e)

    # 🔍 Now open search
    # Scroll to top before opening search
    await page.evaluate("window.scrollTo(0, 0)")
    await page.mouse.wheel(0, -10000)
    await asyncio.sleep(1)

    try:
        search_icon = page.locator("svg.modal__toggle-open.icon-search")
        await search_icon.wait_for(state="visible", timeout=10000)
        await search_icon.click()
    except Exception as e:
        print("❌ Failed to open search modal:", e)
        return []

    await page.wait_for_selector("input#Search-In-Modal", timeout=10000)
    search_input = page.locator("input#Search-In-Modal")
    await search_input.fill(product_name)
    await search_input.press("Enter")

    await page.wait_for_selector("#ProductGridContainer .product-card", timeout=15000)
    products = page.locator("#ProductGridContainer .product-card")

    results = []
    total = await products.count()
    for i in range(min(count, total)):
        product = products.nth(i)
        try:
            title = await product.locator(".product-title-ellipsis").inner_text()
            price = await product.locator(".product-price").inner_text()
            link = await product.locator(".product-title-ellipsis").get_attribute("href")
            img = await product.locator("img").get_attribute("src")

            results.append({
                "title": title,
                "price": price,
                "link": link,
                "image": img
            })
        except Exception as e:
            print(f"❌ Skipped product {i}: {e}")

    if not results:
        print("⚠️ No valid products found.")
        return []

    return results


# ✅ Checkout process
async def proceed_to_checkout(page, send_update=None, user_id=None):
    await _send("🛒 Proceeding to checkout...", send_update)
    print("\n🛒 Proceeding to checkout...")

    try:
        await page.locator("a[href='/cart']").click()
        await _send("🛒 Cart opened.", send_update)
    except Exception as e:
        await _send(f"❌ Failed to open cart: {e}", send_update)
        return

    await page.wait_for_timeout(2000)

    try:
        view_cart = page.locator("button#drawer-cart-button")
        await expect(view_cart).to_be_visible(timeout=5000)
        await view_cart.click()
        #await _send("👀 View Cart button in sidebar clicked.", send_update)
    except Exception as e:
        await _send(f"❌ Failed to click View Cart: {e}", send_update)
        return

    await page.wait_for_timeout(2000)

    try:
        await page.wait_for_selector(".totals__subtotal-value", timeout=5000)
        total_price = await page.locator(".totals__subtotal-value").inner_text()

        quantity_text = "0"
        cart_count = page.locator(".cart-count-bubble .count")
        for _ in range(10):
            quantity_text = await cart_count.inner_text()
            if quantity_text.strip().isdigit() and quantity_text.strip() != "0":
                break
            await page.wait_for_timeout(500)

        summary = f"\n🧾 Order Summary:\n- Total items: {quantity_text}\n- Subtotal: {total_price}"
        print(summary)
        await _send(summary, send_update)
    except Exception as e:
        await _send(f"⚠️ Failed to read order summary: {e}", send_update)

    # Send confirmation buttons
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Order", callback_data="confirm_order")],
        [InlineKeyboardButton("➕ Add More Items", callback_data="add_more")]
    ])
    await send_update(message="👇 Please confirm your order:", reply_markup=keyboard)

    # Wait for Telegram reply
    response = await wait_for_order_confirmation(user_id)  # Reuse same function

    if response == "confirm_order":
        await _send("🛒 Proceeding with order...", send_update)
        # continue with checkout logic
        try:
            await page.locator("#drawer-checkout-button").click()
            await _send("➡️ Proceeding to checkout...", send_update)
        except Exception as e:
            await _send(f"❌ Failed to click checkout: {e}", send_update)
            return

        await page.wait_for_timeout(5000)

        try:
            await page.locator("input#email").fill("testuser@example.com")
            await page.locator("input#first_name").fill("Test")
            await page.locator("input#last_name").fill("User")
            await page.locator("input#phone").fill("03001234567")
            await _send("📨 Dummy contact info filled.", send_update)
        except Exception as e:
            await _send(f"❌ Failed to fill contact form: {e}", send_update)
            return

        try:
            await page.get_by_role("button", name="Continue to shipping").click()
            await _send("🚚 Continuing to shipment...", send_update)
        except Exception as e:
            await _send(f"❌ Failed to continue to shipping: {e}", send_update)
            return

        await page.wait_for_timeout(5000)

        try:
            await page.get_by_role("button", name="Continue to payment").click()
            await _send("💳 Continuing to payment...", send_update)
        except Exception as e:
            await _send(f"❌ Failed to continue to payment: {e}", send_update)
            return

        # ✅ Send payment link to user
        try:
            current_url = page.url
            await _send(f"💳 Click here to complete your payment ({current_url})", send_update)
        except Exception as e:
            await _send(f"⚠️ Failed to get payment URL: {e}", send_update)

    elif response == "add_more":
        await _send("✏️ Okay! Send me the additional items you'd like to add.", send_update)
        return  # You can exit the function or handle differently
    else:
        await _send("❌ No valid response. Cancelling checkout.", send_update)
        return


# 🔄 Optional Telegram update function
async def _send(message, func):
    if func:
        await func(message)
