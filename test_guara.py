from typing import Any, Tuple

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from guara.transaction import Application, AbstractTransaction, IAssertion
from guara import it


class CustomApp(Application):
    def __init__(self, driver=None):
        super().__init__(driver)

    # Execute transactions
    def dado_que(self, transaction, **kwargs):
        super().at(transaction, **kwargs)
        return self

    def quando(self, transaction, **kwargs):
        super().at(transaction, **kwargs)
        return self

    # Validations
    def entao(self, assertion, expected):
        super().asserts(assertion, expected)
        return self

    def espera_se(self, assertion, expected):
        super().asserts(assertion, expected)
        return self


class ClienteEstaLogado(AbstractTransaction):
    """
    Login documentation

    Args:
        with_user (str): the user name
        with_password (str): user password
    """

    def __init__(self, driver):
        self._driver: webdriver.Chrome = driver

    def do(self, com_usuario, com_senha):
        self._driver.get("https://www.saucedemo.com/")
        self._driver.find_element(By.ID, "user-name").send_keys(com_usuario)
        self._driver.find_element(By.ID, "password").send_keys(com_senha)
        self._driver.find_element(By.ID, "login-button").click()
        return "Logou com Sucesso"


class ClienteAdicionaProdutoAoCarrinho(AbstractTransaction):
    """Add product to cart

    Args:
        wait (WebDriverWait): wait for an specific condition
        foo (Any): it is just a dummy parameter
    """

    def __init__(self, driver):
        self._driver: webdriver.Chrome = driver

    def do(self, espere_por):
        espere_por.until(EC.url_contains("inventory"))
        add_to_cart_button = espere_por.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn_inventory"))
        )
        add_to_cart_button.click()
        cart_badge = espere_por.until(
            EC.visibility_of_element_located((By.CLASS_NAME, "shopping_cart_badge"))
        )
        return cart_badge.text

    def undo(self):
        print("Undo product to cart")


class ClienteAbreOCarrinho(AbstractTransaction):
    def do(self, espere_por):
        cart_link = self._driver.find_element(By.CLASS_NAME, "shopping_cart_link")
        cart_link.click()
        cart_title = espere_por.until(EC.visibility_of_element_located((By.CLASS_NAME, "title")))
        assert cart_title.text == "Your Cart"
        cart_quantity = self._driver.find_element(By.CLASS_NAME, "cart_quantity")
        return cart_quantity.text

    def undo(self):
        print("Undo open cart")


# Implements a new assertion to check variations of the expected value
class ReceberAMensagem(IAssertion):
    def __init__(self):
        super().__init__()

    def asserts(self, actual, expected):
        if actual.lower() == expected.lower():
            return True
        raise AssertionError

class AQuantidadeDeveSerIgualA(it.IsEqualTo):
    pass

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    options.add_experimental_option(
        "prefs",
        {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
        },
    )
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 10)
    app = CustomApp(driver)
    yield app, wait
    app.undo()
    driver.quit()

"""
Funcionalidade: Gerenciamento do Carrinho de Compras

  Cenário: Adicionar um produto ao carrinho com sucesso
    Dado que o cliente está logado com o usuário "standard_user" e a senha "secret_sauce"
    E o login é realizado com sucesso
    Quando o cliente adiciona um produto ao carrinho
    Então a quantidade de itens no carrinho deve ser igual a "1"
    Quando o cliente abre o carrinho
    Então a quantidade exibida no carrinho deve ser igual a "1"

"""

def test_add_product_to_cart(driver: Tuple[CustomApp, Any]):
    no_ecommerce, finalizacao = driver
    (
        no_ecommerce.dado_que(
            ClienteEstaLogado,
            com_usuario="standard_user",
            com_senha="secret_sauce"
        )
        .espera_se(ReceberAMensagem, "logou com sucesso")
        .quando(ClienteAdicionaProdutoAoCarrinho, espere_por=finalizacao)
        .entao(AQuantidadeDeveSerIgualA, "1")
        .quando(ClienteAbreOCarrinho, espere_por=finalizacao)
        .entao(AQuantidadeDeveSerIgualA, "1")
    )
