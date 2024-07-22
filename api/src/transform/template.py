from ${mod_path} import ${target_symbol} as lambda_function

try:
    lambda_handler = lambda_function.as_lambda_function_url_handler()
except Exception as e:
    def lambda_handler(evt, ctx):
        full_path = "${mod_path}" + ":" + "${target_symbol}"
        return {
            "statusCode": 500,
            "body": f"Lambda for '{full_path}' failed to start: {e}"
        }
