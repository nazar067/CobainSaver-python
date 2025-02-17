from aiogram.types import LabeledPrice
from localisation.get_language import get_language
from localisation.translations.finance import translations as finance_translation

async def process_payment(callback, amount, provider_token, pool):
    """
    Генерация инвойса для платежа
    """
    user_language = await get_language(pool, callback.message.chat.id)
    prices = [LabeledPrice(label=f"XTR", amount=amount)]
    return dict(
        title=finance_translation["payment_title"][user_language],
        description=finance_translation["payment_description"][user_language].format(amount=amount),
        provider_token=provider_token,
        currency="XTR",
        prices=prices,
        payload=f"user_id:{callback.from_user.id}"
    )
