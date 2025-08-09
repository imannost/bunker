import parsing
import generate

def main():
    spreadsheet_id = "1dzufUPb0ONrTXV7Vk8az5VuQGb81Nmb_F7cNst1-SS4"
    gid_users = "1858649706"
    gid_cards = "707566028"
    output_file = "result.json"

    data = parsing.parse_google_sheet_to_json(spreadsheet_id, gid_users, skip_rows=1, output_file=output_file)
    data_card = parsing.parse_google_sheet_to_json(spreadsheet_id, gid_cards, skip_rows=0, output_file="result_cards.json")

    count = 5
    generate.create_random_dicts_and_save(data, data_card, count, prefix="random_result")

if __name__ == "__main__":
    main()
