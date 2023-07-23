

def pay(payment):
    payment.status = "PAID"
    payment.save()
