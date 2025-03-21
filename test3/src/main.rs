use rusqlite::Connection;

fn main() {
    let conn = Connection::open("../data.db").unwrap();
    let mut stmt = conn.prepare("SELECT COUNT(*) FROM nodes").unwrap();
    let count: i64 = stmt.query_row([], |row| row.get(0)).unwrap();
    println!("Node count: {}", count);
} 